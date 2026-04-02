--------------------------------------student table 
set serveroutput on;
create table students (
  student_id int primary key,
  s_name varchar(50)
  );
  
create or replace procedure populate_stud( sid in NUMBER, name in VARCHAR2) is
begin
  insert into students values(sid, name);
end;
/

begin
  populate_stud(1, 'Alex');
  
end;
/
select * from students;
---------------------------------------------subjects table
create table subjects (
  subj_id int primary key,
  sub_name varchar(50),
  difficulty_level varchar(20)
);

create or replace procedure populate_subjects(subid in number, subname in varchar2, diff_level in varchar2) is
begin
  insert into subjects values(subid, subname, diff_level);
end;
/

BEGIN
    populate_subjects(101, 'DBMS', 'MEDIUM');
    populate_subjects(102, 'OS', 'HARD');
    populate_subjects(103, 'Stochastic Process', 'HARD');
    populate_subjects(104, 'Computer Networks (CN)', 'EASY');
    populate_subjects(105, 'Optimization Techniques', 'EASY');
    populate_subjects(106, 'OS Lab', 'HARD');
    populate_subjects(107, 'CN Lab', 'HARD');
    populate_subjects(108, 'DBMS Lab', 'EASY');

    
END;
/
select * from subjects;

---------------------------------------------study session
CREATE TABLE study_sessions (
  session_id int primary key,
  student_id int,
  subj_id int,
  session_date date,
  duration_hours int,
  FOREIGN KEY (student_id) REFERENCES students(student_id),
  FOREIGN KEY (subj_id) REFERENCES subjects(subj_id)
);

create or replace procedure populate_sessions(sid in number, stuid in number, subjid in number, sess_date in date, dur_hours in number) is
begin
  insert into study_sessions values(sid, stuid, subjid, sess_date, dur_hours);
end;
/
BEGIN
    populate_sessions(1, 1, 101, to_date('2024-06-01', 'YYYY-MM-DD'), 2);
    populate_sessions(2, 1, 102, to_date('2024-06-03', 'YYYY-MM-DD'), 3);
    populate_sessions(3, 1, 103, to_date('2024-06-10', 'YYYY-MM-DD'), 1);
    populate_sessions(4, 1, 104, to_date('2024-06-01', 'YYYY-MM-DD'), 2);
    populate_sessions(5, 1, 105, to_date('2024-06-02', 'YYYY-MM-DD'), 3);
    populate_sessions(6, 1, 106, to_date('2024-06-03', 'YYYY-MM-DD'), 1);
    populate_sessions(7, 1, 107, to_date('2024-06-01', 'YYYY-MM-DD'), 2);
    populate_sessions(8, 1, 108, to_date('2024-06-02', 'YYYY-MM-DD'), 3);

    
END;
/
select * from study_sessions;

-----------------------------------------------------total time per week
create or replace function total_time_per_week return number is
  total_hours number := 0;
begin
  select sum(duration_hours) into total_hours from study_sessions;
  return total_hours;
end;
/

----------------------------------------------------average time per subject
create or replace function avg_time_per_subject return number is
  avg_hours number := 0;
begin
    select avg(duration_hours) into avg_hours from study_sessions; 
  return avg_hours;
end;
/
