create table board_roles (
    board_id serial references boards(board_id),
    role_id serial references roles(role_id),
    primary key (board_id, role_id)
);

update forum_schema_version set version = 6;
