from typing import List

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.database import db
from app.models import (
    Chat,
    ChatMessage,
    ChatSummary,
    ChatMessageRole,
    GeneratedMedia,
    GeneratedImage,
    GeneratedMediaType,
    User,
)

from app.lib.fs_utils import delete_file

from app.services.app_llm import AppLlm
from app.services.image_gen import ImageGen


class ChatManager:
    def __init__(
        self,
        db_uri: str,
        app_llm: AppLlm,
        image_gen: ImageGen,
        images_dir_url_path: str,
    ):
        self.db_uri = db_uri
        self.app_llm = app_llm
        self.image_gen = image_gen
        self.images_dir_url_path = images_dir_url_path

        self.use_rag = False
        self.use_summaries = False

        # For threaded code
        self.engine = create_engine(db_uri)
        self.SessionFactory = sessionmaker(bind=self.engine)

    def create_new_session(self) -> Session:
        return self.SessionFactory()

    def create_chat_and_add_user(self, title: str, user: User) -> Chat:
        chat = Chat(title=title)
        chat.users.append(user)
        self._save_to_db(chat)

        return chat

    def delete_chat_content(self, chat: Chat) -> None:
        try:
            db.session.execute(db.delete(ChatSummary).where(ChatSummary.chat == chat))

            generated_medias = db.session.execute(
                select(
                    ChatMessage.generated_media_id,
                    GeneratedMedia.filename,
                    GeneratedMedia.type,
                )
                .join(
                    GeneratedMedia, ChatMessage.generated_media_id == GeneratedMedia.id
                )
                .where(
                    ChatMessage.chat == chat,
                    ChatMessage.generated_media_id.is_not(None),
                )
            ).all()

            generated_media_ids = [row.generated_media_id for row in generated_medias]

            db.session.execute(db.delete(ChatMessage).where(ChatMessage.chat == chat))

            if generated_media_ids:
                db.session.execute(
                    db.delete(GeneratedMedia).where(
                        GeneratedMedia.id.in_(generated_media_ids)
                    )
                )

                for row in generated_medias:
                    if row.type == GeneratedMediaType.GENERATED_IMAGE:
                        filepath = self.image_gen.get_image_filepath(
                            filename=row.filename
                        )
                        delete_file(filepath=filepath)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def create_chat_message(
        self,
        content: str,
        chat: Chat,
        user: User | None = None,
    ) -> ChatMessage:
        chat_message = ChatMessage(
            content=content, role=ChatMessageRole.ASSISTANT, chat=chat
        )

        if user:
            chat_message.user = user
            chat_message.role = ChatMessageRole.USER

        self._save_to_db(chat_message)

        return chat_message

    def get_generated_image_and_save_messages(
        self,
        image_filename: str,
        prompt: str,
        chat: Chat,
        user: User | None = None,
    ) -> ChatMessage:
        user_chat_message = ChatMessage(
            content=prompt, role=ChatMessageRole.USER, chat=chat, user=user
        )

        generated_image = GeneratedImage(
            filename=image_filename, prompt=prompt, user=user
        )

        chat_message = ChatMessage(
            content=generated_image.as_image_tag(
                image_dir_path=self.images_dir_url_path
            ),
            role=ChatMessageRole.ASSISTANT,
            chat=chat,
            generated_media=generated_image,
        )

        self._save_to_db([user_chat_message, generated_image, chat_message])

        return chat_message

    def get_llm_response_stream_and_save_messages(
        self,
        chat: Chat,
    ):
        session = self.create_new_session()
        session.add(chat)

        response = self.app_llm.get_llm_response_stream(
            messages=chat.messages_as_llm_format(use_summary=self.use_summaries),
            use_rag=self.use_rag,
        )

        full_response = ""

        try:
            for token in response:
                full_response += token

                yield token
        finally:
            # Todo: better way to do this? db.session didn't work
            # Create chat message for LLM response after the stream closes
            # Access sql alchemy directly since this happens after the response closes?
            # https://stackoverflow.com/a/41014157
            response_message = ChatMessage(
                content=full_response.strip(), role=ChatMessageRole.ASSISTANT, chat=chat
            )

            try:
                session.add(response_message)

                if self.use_summaries:
                    # summary generation could take awhile commit it separately
                    # TODO account for token limit if not re-feeding summary
                    # and using raw messages?
                    # TODO use thread or background task
                    # Prevent race conditions
                    summary = self.app_llm.get_chat_summary(
                        chat_messages=chat.chat_messages
                    )

                    if response_message.chat.chat_summary is None:
                        chat_summary = ChatSummary(
                            content=summary,
                            last_message=response_message,
                            chat=response_message.chat,
                        )
                    else:
                        chat_summary = response_message.chat.chat_summary
                        chat_summary.content = summary
                        chat_summary.last_message = response_message

                    session.add(chat_summary)

                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

    def _exists(self, model_class: object) -> bool:
        return db.session.execute(select(model_class).limit(1)).scalar() is not None

    def _save_to_db(self, objects: object | List[object]) -> None:
        try:
            if isinstance(objects, list):
                db.session.add_all(objects)
            else:
                db.session.add(objects)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e

    def _delete_from_db(self, object: object) -> None:
        try:
            db.session.delete(object)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e
