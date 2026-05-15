"""
Serializer per le entità del registro scolastico.

Ogni serializer espone campi leggibili (student_name, subject_name, class_name)
calcolati via SerializerMethodField: sono sempre read-only e non influenzano
la logica di scrittura (create/update).

Regole di scrittura:
  AbsenceSerializer   → is_justified / justification read_only;
                        scrivibili solo nell'action `justify`.
  TardinessSerializer → stessa logica; entry_time scrivibile solo via PATCH.
"""

from rest_framework import serializers

from core.models import (
    SchoolClass,
    StudentEnrollment,
    TeacherAssignment,
    TeacherClassSubject,
    Grade,
    StudentNote,
    Homework,
    Absence,
    Tardiness,
    Lesson,
)


# ==============================================================================
# SchoolClass
# ==============================================================================

class SchoolClassSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SchoolClass
        fields = ["id", "name", "school_year", "tenant"]
        read_only_fields = ["tenant"]


# ==============================================================================
# Enrollment & Assignment
# ==============================================================================

class StudentEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model  = StudentEnrollment
        fields = ["id", "student", "school_class", "date_start", "date_end", "student_name"]

    def get_student_name(self, obj):
        return obj.student.role.user.get_full_name()


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TeacherAssignment
        fields = ["id", "teacher", "date_start", "date_end"]


class TeacherClassSubjectSerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()
    class_name   = serializers.SerializerMethodField()

    class Meta:
        model  = TeacherClassSubject
        fields = ["id", "assignment", "school_class", "subject", "subject_name", "class_name"]

    def get_subject_name(self, obj):
        return obj.subject.name

    def get_class_name(self, obj):
        return obj.school_class.name


# ==============================================================================
# Lesson
# ==============================================================================

class LessonSerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()
    class_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Lesson
        fields = [
            "id",
            "teacher_class_subject",
            "date",
            "hour",
            "description",
            "subject_name",
            "class_name",
        ]

    def get_subject_name(self, obj):
        return obj.teacher_class_subject.subject.name

    def get_class_name(self, obj):
        return obj.teacher_class_subject.school_class.name


# ==============================================================================
# Grade
# ==============================================================================

class GradeSerializer(serializers.ModelSerializer):
    # Campi leggibili aggiunti per il frontend — sempre read-only
    student_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    class_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Grade
        fields = [
            "id",
            "student_enrollment",
            "teacher_class_subject",
            "lesson",
            "date",
            "value",
            "description",
            "student_name",
            "subject_name",
            "class_name",
        ]

    def get_student_name(self, obj):
        return obj.student_enrollment.student.role.user.get_full_name()

    def get_subject_name(self, obj):
        return obj.teacher_class_subject.subject.name

    def get_class_name(self, obj):
        return obj.teacher_class_subject.school_class.name


# ==============================================================================
# StudentNote
# ==============================================================================

class StudentNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StudentNote
        fields = [
            "id",
            "student_enrollment",
            "teacher_assignment",
            "lesson",
            "date",
            "description",
            "is_disciplinary",
        ]


# ==============================================================================
# Homework
# ==============================================================================

class HomeworkSerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()
    class_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Homework
        fields = [
            "id",
            "teacher_class_subject",
            "lesson",
            "assigned_date",
            "due_date",
            "description",
            "subject_name",
            "class_name",
        ]

    def get_subject_name(self, obj):
        return obj.teacher_class_subject.subject.name

    def get_class_name(self, obj):
        return obj.teacher_class_subject.school_class.name


# ==============================================================================
# Absence
# ==============================================================================

class AbsenceSerializer(serializers.ModelSerializer):
    """
    Serializer base per le assenze.
    is_justified e justification sono read_only.
    Per la giustifica si usa AbsenceJustifySerializer.
    """
    student_name = serializers.SerializerMethodField()
    class_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Absence
        fields = [
            "id",
            "student_enrollment",
            "teacher_assignment",
            "lesson",
            "date",
            "is_justified",
            "justification",
            "student_name",
            "class_name",
        ]
        read_only_fields = ["is_justified", "justification"]

    def get_student_name(self, obj):
        return obj.student_enrollment.student.role.user.get_full_name()

    def get_class_name(self, obj):
        return obj.student_enrollment.school_class.name


class AbsenceJustifySerializer(serializers.ModelSerializer):
    """Usato solo nell'action `justify`. Permette di scrivere is_justified e justification."""

    class Meta:
        model  = Absence
        fields = ["is_justified", "justification"]


# ==============================================================================
# Tardiness
# ==============================================================================

class TardinessSerializer(serializers.ModelSerializer):
    """
    Serializer base per i ritardi.
    is_justified e justification sono read_only.
    """

    class Meta:
        model  = Tardiness
        fields = [
            "id",
            "student_enrollment",
            "teacher_assignment",
            "lesson",
            "date",
            "entry_time",
            "needs_justification",
            "is_justified",
            "justification",
        ]
        read_only_fields = ["is_justified", "justification"]


class TardinessJustifySerializer(serializers.ModelSerializer):
    """Usato solo nell'action `justify`."""

    class Meta:
        model  = Tardiness
        fields = ["is_justified", "justification"]


class TardinessUpdateEntryTimeSerializer(serializers.ModelSerializer):
    """Serializer per PATCH entry_time da parte dell'insegnante."""

    class Meta:
        model  = Tardiness
        fields = ["entry_time"]
