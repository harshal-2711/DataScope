"""Education, EdTech, and Academic Performance domain blueprints (Domains 20, 21, 22)."""
from __future__ import annotations

from app.domains.base import (
    ChartRule,
    ComparisonRule,
    DomainBlueprint,
    EntityRule,
    KpiRule,
    RecommendationRule,
    RiskRule,
    TrendRule,
)

DOMAINS: list[DomainBlueprint] = [
    # 20. Education
    DomainBlueprint(
        id="education",
        name="Education",
        description="Schools, universities, institutional courses, student enrollments, faculty teaching loads, and institutional attendance.",
        keywords=("school", "university", "faculty", "course", "curriculum", "enrollment", "semester", "tuition", "campus", "degree", "instructor"),
        alternative_domains=("EdTech", "Academic and Student Performance"),
        entities=(
            EntityRule("student", "Student", ("student_id", "pupil_id", "enrollee_id")),
            EntityRule("course", "Academic Course", ("course_id", "subject_id", "class_id", "module")),
            EntityRule("instructor", "Faculty / Instructor", ("instructor_id", "professor", "teacher_id")),
        ),
        kpis=(
            KpiRule("total_enrollment", "Total Student Enrollment", "Total distinct students registered for courses", ("categorical", "identifier"), metric_patterns=(), dimension_patterns=("student_id", "pupil_id"), formula="count_distinct", format="number", business_meaning="Institutional student body size"),
            KpiRule("avg_class_size", "Average Class Size", "Mean number of students enrolled per academic course", ("numeric",), metric_patterns=("class_size", "enrolled_count"), formula="mean", format="number", business_meaning="Faculty instructional ratio"),
        ),
        charts=(
            ChartRule("enrollment_by_dept", "Enrollment by Academic Department", "bar", dimension_patterns=("department", "faculty", "program"), metric_patterns=("student_id", "enrollment"), aggregation="count", business_question="Which academic departments attract the largest student enrollment?"),
        ),
        comparisons=(
            ComparisonRule("category", "Student Enrollment across Degree Programs", ("program", "degree"), ("student_id", "enrollment")),
        ),
        trends=(
            TrendRule(("student_id", "enrollment"), ("semester", "year", "date"), "Tracking multi-year institutional enrollment trends"),
        ),
        risks=(
            RiskRule("enrollment_drop", "Departmental Enrollment Contraction", "drop", metric_patterns=("student_id", "enrollment"), threshold=0.25, label="Potential anomaly", recommended_action="Review program curriculum market demand and student recruitment marketing."),
        ),
        recommendations=(
            RecommendationRule("operational_efficiency", "avg_class_size", "unbalanced_classes", "Consolidate low-enrollment course sections to optimize faculty allocation.", "Dependent on degree graduation requirements."),
        ),
    ),

    # 21. EdTech
    DomainBlueprint(
        id="edtech",
        name="EdTech",
        description="Online learning platforms, digital courses, video completion rates, quiz submissions, learner progression, and certificates.",
        keywords=("edtech", "lms", "learner", "lesson", "completion_rate", "quiz_score", "course_progress", "video_watched", "certificate", "module_complete"),
        alternative_domains=("Education", "Product Analytics", "Academic and Student Performance"),
        entities=(
            EntityRule("learner", "Online Learner", ("learner_id", "user_id", "student_id")),
            EntityRule("lesson", "Digital Lesson / Module", ("lesson_id", "module_id", "video_id")),
        ),
        kpis=(
            KpiRule("course_completion_rate", "Course Completion Rate", "Percentage of enrolled learners completing full curriculum", ("numeric", "boolean"), metric_patterns=("is_completed", "completion_rate", "completed"), formula="mean", format="percentage", business_meaning="Learner curriculum persistence"),
            KpiRule("avg_quiz_score", "Average Quiz / Assessment Score", "Mean score achieved on modular knowledge checks", ("numeric",), metric_patterns=("quiz_score", "score", "grade"), formula="mean", format="number", business_meaning="Digital learning mastery"),
        ),
        charts=(
            ChartRule("completion_by_course", "Completion Rate by Online Course", "bar", dimension_patterns=("course_title", "course_name", "category"), metric_patterns=("is_completed", "completion_rate"), aggregation="mean", business_question="Which online courses achieve the highest learner completion rates?"),
        ),
        comparisons=(
            ComparisonRule("category", "Quiz Scores across Learning Modules", ("module_name", "subject"), ("quiz_score", "score")),
        ),
        trends=(
            TrendRule(("learner_id", "completions"), ("date", "month"), "Monitoring digital learner active engagement over time"),
        ),
        risks=(
            RiskRule("dropoff_bottleneck", "Module Drop-Off Bottleneck", "drop", metric_patterns=("is_completed", "progress"), threshold=0.5, label="Requires investigation", recommended_action="Redesign early module exercises that exhibit disproportionate learner drop-off."),
        ),
        recommendations=(
            RecommendationRule("product_optimization", "course_completion_rate", "low_completion", "Introduce bite-sized video lessons and automated progress reminder nudges.", "Relies on learner notification opt-in."),
        ),
    ),

    # 22. Academic and Student Performance
    DomainBlueprint(
        id="academic_performance",
        name="Academic and Student Performance",
        description="Exam grades, GPAs, test scores, attendance records, homework submissions, and student at-risk indicators.",
        keywords=("gpa", "exam_score", "test_score", "grade", "attendance_rate", "pass_rate", "student_performance", "homework", "assessment", "at_risk", "student", "score", "attendance", "subject", "marks"),
        alternative_domains=("Education", "EdTech"),
        entities=(
            EntityRule("student", "Student", ("student_id", "student_name", "roll_no")),
            EntityRule("exam", "Exam / Assessment", ("exam_id", "assessment_id", "term")),
        ),
        kpis=(
            KpiRule("avg_gpa", "Average Student GPA / Grade", "Mean grade point average across student body", ("numeric",), metric_patterns=("gpa", "grade", "score", "percentage"), formula="mean", format="number", business_meaning="Overall academic achievement level"),
            KpiRule("pass_rate", "Assessment Pass Rate", "Percentage of students achieving passing grade threshold", ("numeric", "boolean"), metric_patterns=("is_passed", "passed", "pass_fail"), formula="mean", format="percentage", business_meaning="Cohort academic qualification success"),
            KpiRule("avg_attendance", "Average Student Attendance Rate", "Mean percentage of required class sessions attended", ("numeric",), metric_patterns=("attendance", "attendance_rate", "present_days"), formula="mean", format="percentage", business_meaning="Student engagement and classroom presence"),
        ),
        charts=(
            ChartRule("grade_distribution", "Grade / Score Distribution", "histogram", metric_patterns=("score", "grade", "gpa"), aggregation="count", business_question="What is the distribution of student exam scores?"),
            ChartRule("attendance_vs_score", "Attendance vs Exam Score Correlation", "scatter", metric_patterns=("score", "gpa"), dimension_patterns=(), aggregation="sum", business_question="Is high attendance correlated with superior academic scores?"),
        ),
        comparisons=(
            ComparisonRule("category", "Pass Rates by Subject / Course", ("subject", "course"), ("is_passed", "score")),
        ),
        trends=(
            TrendRule(("score", "gpa"), ("exam_date", "term", "year"), "Tracking student achievement progression across semesters"),
        ),
        risks=(
            RiskRule("chronic_absenteeism", "Chronic Absenteeism Anomaly", "drop", metric_patterns=("attendance", "attendance_rate"), threshold=0.75, label="Requires investigation", recommended_action="Deploy early academic intervention counselors for students with attendance below 75%."),
        ),
        recommendations=(
            RecommendationRule("performance_improvement", "pass_rate", "low_pass_rate", "Provide supplementary peer tutoring and diagnostic practice exams in underperforming subjects.", "Assumes availability of qualified peer tutors."),
        ),
    ),
]
