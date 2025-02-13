import os
import sys
from typing import Union, List

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from services.app_llm import AppLlm

# import threading
# from sqlalchemy.orm import scoped_session
# from sqlalchemy.orm import sessionmaker

# TODO better way to do this (import from parent dir)?
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from database import db
from models import Chat, ChatMessage, ChatSummary, ChatMessageRole, GeneratedImage, User


class ChatManager:
    def __init__(self, db_uri: str, app_llm: AppLlm):
        self.db_uri = db_uri
        self.app_llm = app_llm
        self.use_rag = False
        self.use_summaries = False

    def create_chat_and_add_user(self, title: str, user: User) -> Chat:
        chat = Chat(title=title)
        chat.users.append(user)
        db.session.add(chat)
        db.session.commit()

        return chat

    def delete_chat_messages_and_summary_for_chat(self, chat: Chat, user: User) -> None:
        db.session.execute(db.delete(ChatSummary).where(ChatSummary.chat == chat))
        db.session.commit()

        db.session.execute(db.delete(ChatMessage).where(ChatMessage.chat == chat))
        db.session.commit()

        db.session.execute(db.delete(GeneratedImage).where(GeneratedImage.user == user))
        db.session.commit()

    def create_chat_message(
        self,
        body: str,
        role: ChatMessageRole,
        chat: Chat,
        user: Union[User, None] = None,
    ) -> ChatMessage:
        if user:
            chat_message = ChatMessage(body=body, role=role, chat=chat, user=user)
        else:
            chat_message = ChatMessage(body=body, role=role, chat=chat)

        db.session.add(chat_message)
        db.session.commit()

        return chat_message

    def get_generated_image_and_save_messages(
        self,
        image_filename: str,
        image_dir_path: str,
        prompt: str,
        assistantRole: ChatMessageRole,
        userRole: ChatMessageRole,
        chat: Chat,
        user: Union[User, None] = None,
    ) -> ChatMessage:
        user_chat_message = ChatMessage(
            body=prompt, role=userRole, chat=chat, user=user
        )
        db.session.add(user_chat_message)

        generated_image = GeneratedImage(
            filename=image_filename, prompt=prompt, user=user
        )
        db.session.add(generated_image)

        chat_message = ChatMessage(
            body=generated_image.as_image_tag(image_dir_path=image_dir_path),
            role=assistantRole,
            chat=chat,
            generated_image=generated_image,
        )
        db.session.add(chat_message)

        db.session.commit()

        return chat_message

    def get_llm_response_stream_and_save_messages(
        self,
        assistantRole: ChatMessageRole,
        chat: Chat,
        chat_messages: List[ChatMessage],
        chat_summary: str,
        chat_summary_last_message_id: int,
    ):
        llm_messages = self.format_chat_messages_for_llm(
            chat_messages=chat_messages,
            chat_summary=chat_summary,
            chat_summary_last_message_id=chat_summary_last_message_id,
        )

        full_response = ""
        response = self.app_llm.get_llm_response_stream(
            messages=llm_messages, use_rag=self.use_rag
        )

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
                body=full_response.strip(), role=assistantRole, chat=chat
            )

            engine = create_engine(self.db_uri)

            with Session(engine) as session:
                session.add(response_message)
                session.commit()

                if self.use_summaries:
                    # summary generation could take awhile commit it separately
                    # TODO account for token limit if not re-feeding summary
                    # and using raw messages?
                    # TODO use thread or background task
                    # Prevent race conditions
                    summary = self.app_llm.get_chat_summary(chat_messages=chat_messages)

                    if response_message.chat.chat_summary is None:
                        chat_summary = ChatSummary(
                            body=summary,
                            last_message=response_message,
                            chat=response_message.chat,
                        )
                    else:
                        chat_summary = response_message.chat.chat_summary
                        chat_summary.body = summary
                        chat_summary.last_message = response_message

                    session.add(chat_summary)
                    session.commit()

    def format_chat_messages_for_llm(
        self,
        chat_messages: List[ChatMessage],
        chat_summary: str,
        chat_summary_last_message_id: int,
    ) -> List[dict]:
        if self.use_summaries and chat_summary:
            # replace any messages that are before the summary with the summary
            summary_message = ChatMessage.convert_chat_message_to_llm_format(
                role=ChatMessageRole.USER.value,
                content=f"Here is a summary of previous messages: {chat_summary}",
            )

            new_chat_messages = [
                chat_message.as_llm_format()
                for chat_message in chat_messages
                if chat_message.id > chat_summary_last_message_id
            ]

            new_chat_messages = [summary_message] + new_chat_messages

        else:
            new_chat_messages = list(
                map(
                    lambda chat_message: chat_message.as_llm_format(),
                    chat_messages,
                )
            )

        return new_chat_messages
