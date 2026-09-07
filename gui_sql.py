import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import oracledb

# ── DB CONNECTION ─────────────────────────────────────────────────────────────
DB_USER     = "msc24pt30"
DB_PASSWORD = "msc24pt30"
DB_DSN      = "10.1.67.153:1522/orclNew"

# ── COLORS ────────────────────────────────────────────────────────────────────
BG         = "#1a1a1a"
BG2        = "#2a2a2a"
BG3        = "#333333"
FG         = "#ffffff"
FG2        = "#aaaaaa"
FG3        = "#666666"
CARD_BG    = "#242424"
ROW_ALT    = "#222222"
SEL_BG     = "#2c3e50"
GRN        = "#4caf50"
AMB        = "#ff9800"
RED        = "#e53935"

def get_conn():
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)

# ── DB CALLS (each one maps to your PL/SQL procedure or function) ─────────────
def db_get_subjects():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.subj_id, s.sub_name, s.difficulty_level, p.ca1, p.ca2
                FROM subjects s
                LEFT JOIN performance p ON s.subj_id = p.subj_id
            """)
            return cur.fetchall()

def db_get_sessions():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ss.session_id, s.sub_name, ss.session_date, ss.duration_hours
                FROM study_sessions ss
                JOIN subjects s ON ss.subj_id = s.subj_id
                ORDER BY ss.session_date
            """)
            return cur.fetchall()

def db_add_session(session_id, student_id, subj_id, sess_date, duration):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.callproc("add_session", [session_id, student_id, subj_id, sess_date, duration])
        conn.commit()

def db_update_session(session_id, subj_id, sess_date, duration):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.callproc("update_session", [session_id, subj_id, sess_date, duration])
        conn.commit()

def db_delete_session(session_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.callproc("delete_session", [session_id])
        conn.commit()

def db_total_hours():
    with get_conn() as conn:
        with conn.cursor() as cur:
            r = cur.var(oracledb.NUMBER)
            cur.callfunc("total_time_per_week", r, [])
            return int(r.getvalue() or 0)

def db_avg_score(subj_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            r = cur.var(oracledb.NUMBER)
            cur.callfunc("avg_score_per_subject", r, [subj_id])
            return float(r.getvalue() or 0)

def db_avg_time(subj_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            r = cur.var(oracledb.NUMBER)
            cur.callfunc("avg_time_per_subject", r, [subj_id])
            return float(r.getvalue() or 0)

def db_avg_gap(subj_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            r = cur.var(oracledb.NUMBER)
            cur.callfunc("gap_between_sessions_per_subject", r, [subj_id])
            return float(r.getvalue() or 0)

def db_freq(subj_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            r = cur.var(oracledb.NUMBER)
            cur.callfunc("freq_sessions_per_subject", r, [subj_id])
            return int(r.getvalue() or 0)

def db_next_session_id():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT NVL(MAX(session_id),0)+1 FROM study_sessions")
            return cur.fetchone()[0]

def db_get_student_id():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT student_id FROM students WHERE ROWNUM=1")
            row = cur.fetchone()
            return row[0] if row else 1

def db_insights():
    # calls YOUR main() procedure and reads its DBMS_OUTPUT lines
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.callproc("dbms_output.enable", [None])
            cur.callproc("main", [])
            lines, status_var, line_var = [], cur.var(oracledb.NUMBER), cur.var(oracledb.STRING)
            while True:
                cur.callproc("dbms_output.get_line", [line_var, status_var])
                if status_var.getvalue() != 0:
                    break
                if line_var.getvalue():
                    lines.append(line_var.getvalue())
            return lines if lines else ["No output from main()."]

# ── COLOR HELPERS ─────────────────────────────────────────────────────────────
def score_color(sc):
    return GRN if sc >= 30 else (AMB if sc >= 20 else RED)

def diff_color(d):
    return {"HARD": RED, "MEDIUM": AMB, "EASY": GRN}.get(d, FG2)

def draw_bar(canvas, val, max_val, w=90, h=8):
    canvas.delete("all")
    pct    = val / max_val if max_val else 0
    color  = GRN if pct > 0.6 else (AMB if pct > 0.3 else RED)
    canvas.create_rectangle(0, 0, w, h, fill=BG3, outline="")
    if pct > 0:
        canvas.create_rectangle(0, 0, int(pct * w), h, fill=color, outline="")

# ── APP ───────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Study Tracker — Alex")
        self.geometry("1000x700")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._cache     = []
        self._active    = "subjects"
        self._build()
        self._refresh()

    # ── BUILD UI ──────────────────────────────────────────────────────────────
    def _build(self):
        # title
        tr = tk.Frame(self, bg=BG, padx=20, pady=16)
        tr.pack(fill="x")
        tk.Label(tr, text="Study tracker — Alex",
                 font=("Georgia", 18, "bold"), fg=FG, bg=BG).pack(side="left")
        tk.Label(tr, text="semester · 2024",
                 font=("Georgia", 11), fg=FG2, bg=BG).pack(side="right")

        # metric cards row
        cr = tk.Frame(self, bg=BG, padx=20)
        cr.pack(fill="x", pady=(0, 16))
        self.mv = {}
        for key, title, sub in [
            ("total_hrs",   "Total study hours", "all sessions"),
            ("subjects",    "Subjects",           "active this semester"),
            ("avg_session", "Avg session",        "hours per session"),
            ("best_score",  "Best score avg",     "out of 40"),
        ]:
            c = tk.Frame(cr, bg=CARD_BG, padx=18, pady=14)
            c.pack(side="left", expand=True, fill="both", padx=(0, 10))
            tk.Label(c, text=title, font=("Helvetica", 10), fg=FG2, bg=CARD_BG).pack(anchor="w")
            v = tk.Label(c, text="—", font=("Helvetica", 26, "bold"), fg=FG, bg=CARD_BG)
            v.pack(anchor="w")
            tk.Label(c, text=sub, font=("Helvetica", 9), fg=FG3, bg=CARD_BG).pack(anchor="w")
            self.mv[key] = v

        # section header + tab buttons
        sr = tk.Frame(self, bg=BG, padx=20)
        sr.pack(fill="x", pady=(0, 8))
        tk.Label(sr, text="Subjects & performance",
                 font=("Helvetica", 13, "bold"), fg=FG, bg=BG).pack(side="left")
        bf = tk.Frame(sr, bg=BG)
        bf.pack(side="right")
        self.tbns = {}
        for n, lbl in [("subjects","subjects"),("sessions","sessions"),
                       ("add","+ add session"),("insights","insights")]:
            b = tk.Button(bf, text=lbl, font=("Helvetica", 10),
                          bg=FG if n=="subjects" else BG2,
                          fg=BG if n=="subjects" else FG,
                          activebackground=FG2, activeforeground=BG,
                          relief="flat", padx=14, pady=6, cursor="hand2",
                          command=lambda x=n: self._tab(x))
            b.pack(side="left", padx=3)
            self.tbns[n] = b

        # content
        self.cont = tk.Frame(self, bg=BG, padx=20)
        self.cont.pack(fill="both", expand=True)
        self._build_subj()
        self._build_sess()
        self._build_add()
        self._build_ins()
        self._tab("subjects")

    # ── TAB SWITCH ────────────────────────────────────────────────────────────
    def _tab(self, name):
        self._active = name
        for n, b in self.tbns.items():
            b.config(bg=FG if n==name else BG2, fg=BG if n==name else FG)
        for p in [self.p_subj, self.p_sess, self.p_add, self.p_ins]:
            p.pack_forget()
        {"subjects":self.p_subj,"sessions":self.p_sess,
         "add":self.p_add,"insights":self.p_ins}[name].pack(fill="both", expand=True)

    # ── SUBJECTS PANEL ────────────────────────────────────────────────────────
    def _build_subj(self):
        self.p_subj = tk.Frame(self.cont, bg=BG)

        # column headers
        hdr = tk.Frame(self.p_subj, bg=BG2)
        hdr.pack(fill="x")
        cols = [("subject",200,"w"),("difficulty",90,"center"),
                ("ca1",55,"center"),("ca2",55,"center"),
                ("avg score",85,"center"),("avg gap",90,"center"),
                ("study hrs",120,"center"),("sessions",75,"center")]
        for lbl, w, anc in cols:
            tk.Label(hdr, text=lbl, font=("Helvetica", 9, "bold"),
                     fg=FG2, bg=BG2, width=0, anchor=anc,
                     padx=10, pady=8).pack(side="left", ipadx=2)

        # scrollable area
        outer  = tk.Frame(self.p_subj, bg=BG)
        outer.pack(fill="both", expand=True)
        cv     = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb    = tk.Scrollbar(outer, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        self.subj_fr = tk.Frame(cv, bg=BG)
        win = cv.create_window((0,0), window=self.subj_fr, anchor="nw")
        self.subj_fr.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win, width=e.width))

    def _fill_subj(self, subjects):
        for w in self.subj_fr.winfo_children():
            w.destroy()
        max_hrs = max((db_avg_time(s[0]) for s in subjects), default=1) or 1

        for i, (subj_id, name, diff, ca1, ca2) in enumerate(subjects):
            ca1 = ca1 or 0; ca2 = ca2 or 0
            sc   = db_avg_score(subj_id)
            hrs  = db_avg_time(subj_id)
            gap  = db_avg_gap(subj_id)
            freq = db_freq(subj_id)
            rbg  = BG if i % 2 == 0 else ROW_ALT

            row = tk.Frame(self.subj_fr, bg=rbg)
            row.pack(fill="x")

            # name
            tk.Label(row, text=name, font=("Helvetica", 10, "bold"),
                     fg=FG, bg=rbg, anchor="w", padx=10, pady=10,
                     width=18).pack(side="left")
            # difficulty badge
            df = tk.Frame(row, bg=rbg, padx=10)
            df.pack(side="left")
            tk.Label(df, text=diff, font=("Helvetica", 9, "bold"),
                     fg=diff_color(diff), bg=BG3, padx=8, pady=3).pack()
            # ca1 ca2
            for v in [ca1, ca2]:
                tk.Label(row, text=str(v), font=("Helvetica", 10),
                         fg=FG, bg=rbg, width=5, anchor="center", padx=4).pack(side="left")
            # avg score
            tk.Label(row, text=f"{sc:.1f}", font=("Helvetica", 10, "bold"),
                     fg=score_color(sc), bg=rbg, width=7, anchor="center").pack(side="left")
            # avg gap
            gc = RED if gap > 7 else GRN
            tk.Label(row, text=f"{gap:.1f}d", font=("Helvetica", 10),
                     fg=gc, bg=rbg, width=9, anchor="center").pack(side="left")
            # bar + hrs
            bf2 = tk.Frame(row, bg=rbg, padx=8)
            bf2.pack(side="left")
            bc = tk.Canvas(bf2, width=90, height=8, bg=BG3, highlightthickness=0)
            bc.pack(side="left", pady=2)
            draw_bar(bc, hrs, max_hrs)
            tk.Label(bf2, text=f"{hrs:.0f}h", font=("Helvetica", 9),
                     fg=FG2, bg=rbg, padx=4).pack(side="left")
            # sessions freq
            tk.Label(row, text=str(freq), font=("Helvetica", 10),
                     fg=FG2, bg=rbg, width=6, anchor="center").pack(side="left")

    # ── SESSIONS PANEL ────────────────────────────────────────────────────────
    def _build_sess(self):
        self.p_sess = tk.Frame(self.cont, bg=BG)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("D.Treeview", background=BG2, fieldbackground=BG2,
                        foreground=FG, font=("Helvetica", 10), rowheight=30, borderwidth=0)
        style.configure("D.Treeview.Heading", background=BG3, foreground=FG2,
                        font=("Helvetica", 10, "bold"), relief="flat")
        style.map("D.Treeview", background=[("selected", SEL_BG)], foreground=[("selected", FG)])

        cols = ("ID","Subject","Date","Duration (hrs)")
        self.tree_sess = ttk.Treeview(self.p_sess, columns=cols, show="headings", style="D.Treeview")
        for col, w in zip(cols,[50,300,150,130]):
            self.tree_sess.heading(col, text=col)
            self.tree_sess.column(col, width=w, anchor="w" if col=="Subject" else "center")
        vsb = ttk.Scrollbar(self.p_sess, orient="vertical", command=self.tree_sess.yview)
        self.tree_sess.configure(yscrollcommand=vsb.set)
        self.tree_sess.pack(side="left", fill="both", expand=True, pady=6)
        vsb.pack(side="left", fill="y", pady=6)

        bc = tk.Frame(self.p_sess, bg=BG, padx=12)
        bc.pack(side="left", fill="y", pady=6)
        self._btn(bc, "Edit",   self._edit).pack(fill="x", pady=4)
        self._btn(bc, "Delete", self._delete).pack(fill="x", pady=4)

    # ── ADD SESSION PANEL ─────────────────────────────────────────────────────
    def _build_add(self):
        self.p_add = tk.Frame(self.cont, bg=BG)
        f = tk.Frame(self.p_add, bg=CARD_BG, padx=30, pady=30)
        f.pack(anchor="nw", pady=10)

        tk.Label(f, text="Subject", font=("Helvetica",10), fg=FG2, bg=CARD_BG).grid(
            row=0, column=0, sticky="w", pady=10, padx=(0,20))
        self.var_subj = tk.StringVar()
        self.cb_subj  = ttk.Combobox(f, textvariable=self.var_subj,
                                     state="readonly", width=26, font=("Helvetica",10))
        self.cb_subj.grid(row=0, column=1, sticky="w", pady=10)

        tk.Label(f, text="Date (YYYY-MM-DD)", font=("Helvetica",10), fg=FG2, bg=CARD_BG).grid(
            row=1, column=0, sticky="w", pady=10, padx=(0,20))
        self.var_date = tk.StringVar(value="2024-06-01")
        tk.Entry(f, textvariable=self.var_date, width=18, font=("Helvetica",10),
                 bg=BG3, fg=FG, insertbackground=FG, relief="flat").grid(
            row=1, column=1, sticky="w", pady=10)

        tk.Label(f, text="Duration (hours)", font=("Helvetica",10), fg=FG2, bg=CARD_BG).grid(
            row=2, column=0, sticky="w", pady=10, padx=(0,20))
        self.var_dur = tk.IntVar(value=2)
        tk.Spinbox(f, from_=1, to=12, textvariable=self.var_dur, width=6,
                   font=("Helvetica",10), bg=BG3, fg=FG,
                   buttonbackground=BG3, relief="flat").grid(
            row=2, column=1, sticky="w", pady=10)

        self._btn(f, "Add Session", self._add, accent=True).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(16,0))

    # ── INSIGHTS PANEL ────────────────────────────────────────────────────────
    def _build_ins(self):
        self.p_ins = tk.Frame(self.cont, bg=BG)
        self.ins_txt = tk.Text(self.p_ins, font=("Courier",11),
                               bg=CARD_BG, fg=FG, relief="flat",
                               padx=16, pady=14, wrap="word",
                               state="disabled", insertbackground=FG)
        self.ins_txt.pack(fill="both", expand=True, pady=8)

    # ── BUTTON HELPER ─────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, accent=False):
        return tk.Button(parent, text=text, command=cmd, font=("Helvetica",10),
                         bg=FG if accent else BG3, fg=BG if accent else FG,
                         activebackground=FG2, activeforeground=BG,
                         relief="flat", padx=16, pady=7, cursor="hand2")

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _add(self):
        name = self.var_subj.get()
        sub  = next((s for s in self._cache if s[1]==name), None)
        d    = self.var_date.get().strip()
        dur  = self.var_dur.get()
        if not sub or not d:
            messagebox.showerror("Error", "Fill in all fields."); return
        try:
            import datetime
            db_add_session(db_next_session_id(), db_get_student_id(),
                           sub[0], datetime.datetime.strptime(d,"%Y-%m-%d").date(), dur)
            self._refresh()
            messagebox.showinfo("Done", f"Session added for {name}.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def _edit(self):
        sel = self.tree_sess.selection()
        if not sel: messagebox.showwarning("No selection","Select a session."); return
        v  = self.tree_sess.item(sel[0])["values"]
        sid, sname, sdate, sdur = int(v[0]), v[1], str(v[2]), int(str(v[3]).replace("h",""))
        nd = simpledialog.askinteger("Edit", f"New duration for {sname} (current:{sdur}h):",
                                     initialvalue=sdur, minvalue=1, maxvalue=24)
        if nd is None: return
        try:
            import datetime
            sub = next((s for s in self._cache if s[1]==sname), None)
            db_update_session(sid, sub[0] if sub else None,
                              datetime.datetime.strptime(sdate[:10],"%Y-%m-%d").date(), nd)
            self._refresh()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def _delete(self):
        sel = self.tree_sess.selection()
        if not sel: messagebox.showwarning("No selection","Select a session."); return
        v = self.tree_sess.item(sel[0])["values"]
        if messagebox.askyesno("Confirm", f"Delete session #{v[0]} ({v[1]})?"):
            try:
                db_delete_session(int(v[0])); self._refresh()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

    # ── REFRESH ───────────────────────────────────────────────────────────────
    def _refresh(self):
        try:
            subjects = db_get_subjects()
            sessions = db_get_sessions()
            total    = db_total_hours()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect to Oracle DB.\n\n{e}"); return

        self._cache = subjects
        n = len(sessions)

        # metric cards
        self.mv["total_hrs"].config(text=str(total))
        self.mv["subjects"].config(text=str(len(subjects)))
        self.mv["avg_session"].config(text=str(round(total/n,1) if n else 0))
        best = max((db_avg_score(s[0]) for s in subjects), default=0)
        self.mv["best_score"].config(text=f"{best:.1f}")

        # subject dropdown
        names = [s[1] for s in subjects]
        self.cb_subj["values"] = names
        if names and not self.var_subj.get():
            self.cb_subj.current(0)

        # subjects rows
        self._fill_subj(subjects)

        # sessions
        for r in self.tree_sess.get_children():
            self.tree_sess.delete(r)
        for (sid, sname, sdate, dur) in sessions:
            self.tree_sess.insert("","end", values=(sid, sname, str(sdate)[:10], f"{dur}h"))

        # insights from your main()
        try:
            lines = db_insights()
        except Exception as e:
            lines = [f"Could not run main(): {e}"]
        self.ins_txt.config(state="normal")
        self.ins_txt.delete("1.0","end")
        for l in lines:
            self.ins_txt.insert("end", l+"\n\n")
        self.ins_txt.config(state="disabled")


if __name__ == "__main__":
    App().mainloop()