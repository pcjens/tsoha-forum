alter table posts add column content_original text;
alter table posts add column title_original text;

update forum_schema_version set version = 3;
