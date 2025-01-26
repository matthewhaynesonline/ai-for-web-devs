from datetime import datetime, timezone
from enum import Enum as StandardEnum
from uuid import uuid4, UUID

from typing import Dict, List, Optional, Tuple

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship

from app.database import db

from app.lib.fs_utils import strip_non_alpha_characters

#####
# Lib
#####
ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S"
# "%z not working"
ISO8601_UTC_TZ = "+00:00"
DATETIME_FORMAT = f"{ISO8601_FORMAT}{ISO8601_UTC_TZ}"

MAX_TITLE_CHARACTERS = 64


class IdMixin:
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, default=None, primary_key=True)

    uuid: Mapped[UUID] = mapped_column(
        default_factory=uuid4, nullable=False, unique=True
    )


class TimestampMixin:
    __abstract__ = True

    # Set format for datetime serializer
    # https://github.com/n0nSmoker/SQLAlchemy-serializer/blob/master/README.md#custom-formats
    datetime_format = DATETIME_FORMAT

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


def get_uuid_timestamps(
    record, encode_values: bool = True
) -> Tuple[UUID | str, datetime | str, datetime | str]:
    uuid = record.uuid
    created_at = record.created_at
    updated_at = record.updated_at

    if encode_values:
        uuid = str(uuid)
        created_at = created_at.strftime(record.datetime_format)
        updated_at = updated_at.strftime(record.datetime_format)

    return (uuid, created_at, updated_at)


def get_teaser_text(content: str, max_number_of_words: int = 50) -> str:
    split_token = " "
    words = content.split()

    if len(words) <= max_number_of_words:
        teaser = split_token.join(words)
    else:
        teaser = split_token.join(words[:max_number_of_words])
        teaser += " [...]"

    return teaser


def convert_chat_message_to_llm_format(role: str, content: str) -> Dict[str, str]:
    return {
        "role": role,
        "content": content,
    }


def chat_messages_as_llm_format(
    chat, assistant_role_value, use_summary: bool = False, exclude_media: bool = True
) -> List[Dict[str, str]]:
    if exclude_media:
        messages = [
            chat_message.as_llm_format()
            for chat_message in chat.chat_messages
            if chat_message.generated_media is None
        ]
    else:
        messages = [chat_message.as_llm_format() for chat_message in chat.chat_messages]

    if use_summary and chat.chat_summary:
        # replace any messages that are before the summary with the summary
        summary_message = convert_chat_message_to_llm_format(
            role=assistant_role_value,
            content=f"Here is a summary of previous messages: {chat.chat_summary.content}",
        )

        NUMBER_OF_MESSAGES_TO_INCLUDE_AFTER_SUMMARY = 3

        messages = [summary_message] + messages[
            -NUMBER_OF_MESSAGES_TO_INCLUDE_AFTER_SUMMARY:
        ]

    return messages


def get_image_tag_for_generated_image(
    prompt: str,
    filename: str,
    files_dir_path: str,
    css_classes: str = "img-fluid rounded",
    link_to_image: bool = True,
) -> str:
    image_url = f"{files_dir_path}/{filename}"
    alt_text = strip_non_alpha_characters(input=prompt, replacement_character=" ")
    alt_text = f"generated image of '{alt_text}'"

    image_tag_markup = (
        f'<img class="{css_classes}" src="{image_url}" alt="{alt_text}" />'
    )

    if link_to_image:
        image_tag_markup = (
            f'<a class="d-inline-block" href="{image_url}">{image_tag_markup}</a>'
        )

    return image_tag_markup


########
# Models
########
class BaseModel(MappedAsDataclass, db.Model, IdMixin, TimestampMixin):
    __abstract__ = True


######
# User
######
class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), default=None, nullable=False, unique=True
    )

    chats: Mapped[List["Chat"]] = relationship(
        back_populates="users",
        default_factory=list,
        secondary="chat_users",
        repr=False,
    )

    chat_messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="user",
        default_factory=list,
        order_by="ChatMessage.id",
        repr=False,
    )

    generated_medias: Mapped[List["GeneratedMedia"]] = relationship(
        back_populates="user",
        default_factory=list,
        order_by="GeneratedMedia.id",
        repr=False,
    )

    def __repr__(self) -> str:
        return f"<User {self.username}({self.id})>"

    def to_dict(self, encode_values: bool = True) -> Dict:
        uuid, created_at, updated_at = get_uuid_timestamps(
            record=self, encode_values=encode_values
        )

        # chat_messages = [chat_message.to_dict() for chat_message in self.chat_messages]
        # generated_images = [chat_message.to_dict() for chat_message in self.chat_messages]

        return {
            "username": self.username,
            "id": self.id,
            "uuid": uuid,
            "created_at": created_at,
            "updated_at": updated_at,
        }


######
# Chat
######
class Chat(BaseModel):
    __tablename__ = "chats"

    title: Mapped[Optional[str]] = mapped_column(default=None)

    users: Mapped[List["User"]] = relationship(
        back_populates="chats", default_factory=list, secondary="chat_users", repr=False
    )

    chat_messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="chat",
        default_factory=list,
        order_by="ChatMessage.id",
        passive_deletes=True,
        repr=False,
    )

    chat_summary: Mapped["ChatSummary"] = relationship(
        back_populates="chat", default=None, passive_deletes=True, repr=False
    )

    def __repr__(self) -> str:
        return f"<Chat {self.title}({self.id})>"

    def messages_as_llm_format(
        self, use_summary: bool = False, exclude_media: bool = True
    ) -> List[Dict[str, str]]:
        return chat_messages_as_llm_format(
            chat=self,
            assistant_role_value=ChatMessageRole.ASSISTANT.value,
            use_summary=use_summary,
            exclude_media=exclude_media,
        )

    def to_dict(
        self, encode_values: bool = True, include_chat_summary: bool = False
    ) -> Dict:
        uuid, created_at, updated_at = get_uuid_timestamps(
            record=self, encode_values=encode_values
        )

        # users =
        chat_summary = None
        if include_chat_summary and self.chat_summary:
            chat_summary = self.chat_summary.to_dict()

        chat_messages = [
            chat_message.to_dict() for chat_message in self.chat_messages
        ] or []

        return {
            "title": self.title,
            "id": self.id,
            "uuid": uuid,
            "created_at": created_at,
            "updated_at": updated_at,
            "chat_summary": chat_summary,
            "chat_messages": chat_messages,
        }


class ChatUser(MappedAsDataclass, db.Model):
    __tablename__ = "chat_users"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), default=None)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), default=None)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            chat_id,
            user_id,
        ),
    )

    def __repr__(self) -> str:
        return f"<ChatUser {self.chat_id}-{self.user_id}>"


##############
# Chat Message
##############
class ChatMessageRole(StandardEnum):
    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"


class ChatMessageState(StandardEnum):
    PENDING = "pending"
    READY = "ready"


class ChatMessage(BaseModel):
    @classmethod
    def convert_chat_message_to_llm_format(
        cls, role: str, content: str
    ) -> Dict[str, str]:
        return convert_chat_message_to_llm_format(role=role, content=content)

    __tablename__ = "chat_messages"

    content: Mapped[Text] = mapped_column(Text, default=None, nullable=False)

    role: Mapped[ChatMessageRole] = mapped_column(
        Enum(ChatMessageRole), default=ChatMessageRole.ASSISTANT, nullable=False
    )

    state: Mapped[ChatMessageState] = mapped_column(
        Enum(ChatMessageState), default=ChatMessageState.READY, nullable=False
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), default=None
    )
    chat: Mapped["Chat"] = relationship(
        back_populates="chat_messages",
        default=None,
        foreign_keys=[chat_id],
        overlaps="story_messages",
        repr=False,
    )

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), default=None)
    user: Mapped[Optional["User"]] = relationship(
        back_populates="chat_messages",
        default=None,
        foreign_keys=[user_id],
        overlaps="story_messages",
        repr=False,
    )

    chat_summary: Mapped["ChatSummary"] = relationship(
        back_populates="last_message", default=None, repr=False
    )

    generated_media_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("generated_medias.id"), default=None
    )
    generated_media: Mapped[Optional["GeneratedMedia"]] = relationship(
        back_populates="chat_message",
        default=None,
        foreign_keys=[generated_media_id],
        repr=False,
    )

    @property
    def state_is_pending(self) -> bool:
        return self.state == ChatMessageState.PENDING

    @property
    def state_is_ready(self) -> bool:
        return self.state == ChatMessageState.READY

    @property
    def has_generated_media(self) -> bool:
        return self.generated_media_id is not None

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id}>"

    def as_llm_format(self) -> Dict[str, str]:
        return self.convert_chat_message_to_llm_format(
            role=self.role.value, content=self.content
        )

    def to_dict(
        self, encode_values: bool = True, include_metadata: bool = False
    ) -> Dict:
        uuid, created_at, updated_at = get_uuid_timestamps(
            record=self, encode_values=encode_values
        )

        data = {
            "id": self.id,
            "title": None,
            "content": self.content,
            "role": self.role.value,
            "state": self.state.value,
            "created_at": created_at,
            "updated_at": updated_at,
            "generated_media": self.generated_media.to_dict()
            if self.has_generated_media
            else None,
        }

        if hasattr(self, "title"):
            data["title"] = self.title

        if include_metadata:
            data["chat_id"] = self.chat_id
            data["uuid"] = uuid
            data["user_id"] = self.user_id or None

        return data


class ChatSummary(BaseModel):
    __tablename__ = "chat_summaries"

    content: Mapped[Text] = mapped_column(Text, default=None, nullable=False)

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), default=None
    )
    chat: Mapped["Chat"] = relationship(
        back_populates="chat_summary", default=None, foreign_keys=[chat_id], repr=False
    )

    last_message_id: Mapped[int] = mapped_column(
        ForeignKey("chat_messages.id"), default=None
    )
    last_message: Mapped["ChatMessage"] = relationship(
        back_populates="chat_summary",
        default=None,
        foreign_keys=[last_message_id],
        repr=False,
    )

    def __repr__(self) -> str:
        return f"<ChatSummary {self.id}>"

    def get_teaser(self) -> str | None:
        teaser = None

        if self.content:
            teaser = get_teaser_text(self.content)

        return teaser

    def to_dict(
        self, encode_values: bool = True, include_metadata: bool = False
    ) -> Dict:
        data = {
            "content": self.content,
        }

        if include_metadata:
            uuid, created_at, updated_at = get_uuid_timestamps(
                record=self, encode_values=encode_values
            )

            data["chat_id"] = self.chat_id
            data["id"] = self.id
            data["uuid"] = uuid
            data["created_at"] = created_at
            data["updated_at"] = updated_at

        return data


#######
# Media
#######
class GeneratedMediaType(StandardEnum):
    GENERATED_MEDIA = "generated_media"
    GENERATED_IMAGE = "generated_image"


class GeneratedMedia(BaseModel):
    __tablename__ = "generated_medias"

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": GeneratedMediaType.GENERATED_MEDIA,
    }

    type: Mapped[GeneratedMediaType] = mapped_column(
        Enum(GeneratedMediaType),
        default=GeneratedMediaType.GENERATED_MEDIA,
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(default=None)
    prompt: Mapped[str] = mapped_column(default=None, nullable=False)

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), default=None, use_existing_column=True
    )
    user: Mapped[Optional["User"]] = relationship(
        back_populates="generated_medias",
        default=None,
        foreign_keys=[user_id],
        repr=False,
    )

    chat_message: Mapped["ChatMessage"] = relationship(
        back_populates="generated_media", default=None, repr=False
    )

    def __repr__(self) -> str:
        return f"<GeneratedMedia {self.id}>"

    def to_dict(
        self, encode_values: bool = True, include_metadata: bool = False
    ) -> Dict:
        uuid, created_at, updated_at = get_uuid_timestamps(
            record=self, encode_values=encode_values
        )

        data = {
            "id": self.id,
            "type": self.type.value,
            "filename": self.filename,
            "prompt": self.prompt,
            "created_at": created_at,
            "updated_at": updated_at,
        }

        if include_metadata:
            data["uuid"] = uuid
            data["user_id"] = self.user_id or None

        return data


class GeneratedImage(GeneratedMedia):
    __mapper_args__ = {"polymorphic_identity": GeneratedMediaType.GENERATED_IMAGE}

    def __repr__(self) -> str:
        return f"<GeneratedImage {self.id}>"

    def as_image_tag(
        self,
        image_dir_path: str,
        css_classes: str = "img-fluid rounded",
        link_to_image: bool = True,
    ) -> str:
        return get_image_tag_for_generated_image(
            prompt=self.prompt,
            filename=self.filename,
            files_dir_path=image_dir_path,
            css_classes=css_classes,
            link_to_image=link_to_image,
        )
