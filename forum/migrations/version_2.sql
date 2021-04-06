create table boards (
    board_id serial primary key,
    title text not null,
    description text not null
);

create table topics (
    topic_id serial primary key,
    parent_board_id serial references boards(board_id),
    sticky boolean not null
);

create table posts (
    post_id serial primary key,
    parent_topic_id serial references topics(topic_id),
    author_user_id serial references users(user_id),
    title text not null,
    content text not null,
    creation_time timestamp with time zone not null,
    edit_time timestamp with time zone null
);

update forum_schema_version set version = 2;
