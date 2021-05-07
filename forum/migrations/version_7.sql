alter table boards add column deleted boolean not null default FALSE;

update forum_schema_version set version = 7;
