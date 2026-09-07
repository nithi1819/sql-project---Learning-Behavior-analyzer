--------------------------------------student table 
set serveroutput on;
create table students (
  student_id int primary key,
  s_name varchar(50)
  );
  
create or replace procedure populate_stud( sid in NUMBER, s_name2 in VARCHAR2) is
begin
  insert into students values(sid, s_name2);
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
/
select * from performance;
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

-----------------------------------------------------crud
create or replace procedure add_session(
  p_session_id in number,
  p_student_id in number,
  p_subj_id in number,
  p_date in date,
  p_duration in number
) is
begin
  insert into study_sessions
  values (p_session_id, p_student_id, p_subj_id, p_date, p_duration);

  commit;
end;
/

create or replace procedure view_sessions is
begin
  for rec in (select * from study_sessions) loop
    dbms_output.put_line(
      rec.session_id || ' | ' ||
      rec.student_id || ' | ' ||
      rec.subj_id || ' | ' ||
      rec.session_date || ' | ' ||
      rec.duration_hours
    );
  end loop;
end;
/

create or replace procedure update_session(
  p_session_id in number,
  p_subj_id in number,
  p_date in date,
  p_duration in number
) is
begin
  update study_sessions
  set subj_id = p_subj_id,
      session_date = p_date,
      duration_hours = p_duration
  where session_id = p_session_id;

  commit;
end;
/

create or replace procedure delete_session(
  p_session_id in number
) is
begin
  delete from study_sessions
  where session_id = p_session_id;

  commit;
end;
/


-----------------------------------------------------total time per week
create or replace function total_time_per_week return number is
  total_hours number := 0;
begin
  select sum(duration_hours) into total_hours from study_sessions;
  return total_hours;
end;
/

----------------------------------------------------average time per subject
create or replace function avg_time_per_subject(p_subj_id in number) return number is
  avg_hours number := 0;
begin
    select avg(duration_hours) into avg_hours from study_sessions where subj_id = p_subj_id; 
  return avg_hours;
end;
/

----------------------------------------------------avg_score per subject
create or replace function avg_score_per_subject(p_subj_id in number) return number is
  avg_score number := 0;
  ca1_marks number := 0;
  ca2_marks number := 0;

BEGIN
  select ca1, ca2  into ca1_marks, ca2_marks from performance where subj_id = p_subj_id; 
    avg_score := (ca1_marks + ca2_marks)/2;
  return avg_score;
  end;
/

-----------------------------------------------------gap between study sessions
create or replace function gap_between_sessions_per_subject(p_subj_id in number)
return number IS
  prev_date date := null;
  curr_gap number := 0;
  total_gap number := 0;
  cnt number := 0;

BEGIN
  for rec in (
    select session_date
    from study_sessions
    where subj_id = p_subj_id
    order by SESSION_DATE
  ) LOOP
  
    if prev_date is not null THEN
      curr_gap := rec.session_date - prev_date;
      total_gap := total_gap + curr_gap;
      cnt := cnt + 1;
    end if;

    prev_date := rec.session_date;
  end loop;

  if cnt = 0 THEN
    return 0;
  else
    return total_gap/cnt;
  end if;
end;
/

------------------------------------------------------frequency of study sessions per subject
create or replace function freq_sessions_per_subject(p_subj_id in number) return number is
  freq number := 0;
BEGIN
  select count(*) into freq from study_sessions where subj_id = p_subj_id;
  return freq;
end;
/

-----------------------------------------------------main
create or replace procedure main is
  total_time number;
  avg_time_per_sub number;
  avg_score_per_sub number;
  avg_gap number;
  freq_per_sub number;
  difficulty2 varchar(20);

begin 

  for rec in (select subj_id, DIFFICULTY_LEVEL from subjects)loop
    total_time := total_time_per_week();
    avg_time_per_sub := avg_time_per_subject(rec.subj_id);
    avg_score_per_sub := avg_score_per_subject(rec.subj_id);
    avg_gap := GAP_BETWEEN_SESSIONS_PER_SUBJECT(rec.subj_id);
    freq_per_sub := FREQ_SESSIONS_PER_SUBJECT(rec.subj_id);
    difficulty2 := rec.difficulty_level;

    DBMS_OUTPUT.PUT_LINE('Subject ID: ' || rec.subj_id);

    if avg_gap > 7 then
        dbms_output.PUT_LINE('Weak retention - revise more frequently (Gap: ' || ROUND(avg_gap, 1) || ' days)');
    end if;

    if avg_time_per_sub > 6 and avg_score_per_sub < 20 THEN
        dbms_output.PUT_LINE('Inefficiency - high study time, less marks (Time: ' || ROUND(avg_time_per_sub, 1) || ' hrs | Score: ' || ROUND(avg_score_per_sub, 1) || ')');
    end if;

    if freq_per_sub < 10 and difficulty2 = 'HARD' then
        dbms_output.PUT_LINE('You are not studying enough for hard subjects (Current sessions: ' || freq_per_sub || ', Target: 10+)');
    end if;

    if freq_per_sub < 6 and difficulty2 = 'MEDIUM' then
        dbms_output.PUT_LINE('You are not studying enough for medium subjects (Current sessions: ' || freq_per_sub || ', Target: 6+)');
    end if;

    if freq_per_sub < 3 and difficulty2 = 'EASY' then
        dbms_output.PUT_LINE('You are not studying enough for easy subjects (Current sessions: ' || freq_per_sub || ', Target: 3+)');
    end if;

    if avg_time_per_sub < 6 and avg_score_per_sub > 25 THEN
        dbms_output.PUT_LINE('Strong subject - less effort, high score (Time: ' || ROUND(avg_time_per_sub, 1) || ' hrs | Score: ' || ROUND(avg_score_per_sub, 1) || ')');
    end if;
  end loop;


end;
/

BEGIN
  main();
end;
/


