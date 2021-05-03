alter table users add column csrf_token text null;

update forum_schema_version set version = 4;
