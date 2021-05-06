create table roles (
    role_id serial primary key,
    role_name text not null,
    can_create_boards boolean not null,
    can_create_roles boolean not null,
    can_assign_roles boolean not null
);

insert into roles (
    role_id,
    role_name,
    can_create_boards,
    can_create_roles,
    can_assign_roles
) values (
    1,
    'Admin',
    TRUE,
    TRUE,
    TRUE
);

create table user_roles (
    user_id serial references users(user_id),
    role_id serial references roles(role_id),
    primary key (user_id, role_id)
);

update forum_schema_version set version = 5;
