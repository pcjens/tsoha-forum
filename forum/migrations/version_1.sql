create table users (
    user_id serial primary key,
    username text not null,
    password_hash text,
    creation_time timestamp with time zone not null,
    password_set_time timestamp with time zone,
    latest_login_time timestamp with time zone
);

update forum_schema_version set version = 1;
