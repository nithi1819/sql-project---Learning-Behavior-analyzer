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
----------------------------------------------performance table
CREATE TABLE performance (
  perf_id INT PRIMARY KEY,
  subj_id INT,
  ca1 INT,
  ca2 INT,
  FOREIGN KEY (subj_id) REFERENCES subjects(subj_id)
);

CREATE OR REPLACE PROCEDURE populate_performance(
    perfid IN NUMBER,
    subid IN NUMBER,
    s1 IN NUMBER,
    s2 IN NUMBER
) IS
BEGIN
  INSERT INTO performance VALUES(perfid, subid, s1, s2);
END;
/

BEGIN
    populate_performance(1, 101, 30, 31);
    populate_performance(2, 102, 39, 40);
    populate_performance(3, 103, 24, 32);
    populate_performance(4, 104, 25, 23);
    populate_performance(5, 105, 27, 20);
    populate_performance(6, 106, 24, 29);
    populate_performance(7, 107, 20, 30);
    populate_performance(8, 108, 25, 16);

    
END;

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

----------------------------------------------------avg_score per subject
create or replace function avg_score_per_subject return number is
  avg_score number := 0;

BEGIN
  for i in (select ca1, ca2 from performance) loop
    avg_score := avg_score + (i.ca1 + i.ca2)/2;
  end loop;
  return avg_score;
  end;
/

-----------------------------------------------------gap between study sessions
create or replace function gap_between_sessions return number is
  avg_gap number := 0;
  sum := 0;
BEGIN
  for i in (select session_date, subject_id from study_sessions order by session_date) loop
    for j in (select session_date, subject_id from study_sessions order by session_date) loop
      if i.subject_id == j.subject_id and i.session_date != j.session_date then
        sum := sum + abs(i.session_date - j.session_date);
      end if;
    end loop;   
  end loop;
   select sum/(count(*)) into avg_gap from study_sessions;
  return avg_gap;
end;
/

------------------------------------------------------frequency of study sessions per subject
create or replace function freq_sessions_per_subject return number is
  freq number := 0;
BEGIN
  select count(*) into freq from study_sessions group by subject_id;
  return freq;
end;
/

-------------------------------------------------------