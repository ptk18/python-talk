class CourseRegistration:
    """
    A course registration system for managing a student's courses.
    """

    def __init__(self, student_name, courses=None):
        """
        Create a course registration profile for a student.

        Phrases: create registration, initialize student, start course registration.

        Args:
            student_name: name of the student.
            courses: optional initial list of courses.
        """
        self.student_name = student_name
        self.courses = list(courses) if courses else []

    def add_course(self, course_name):
        """
        Add a new course to the student's registration.

        Phrases: add course, register course, enroll in course, take course.

        Args:
            course_name: name of the course to add.
        """
        if not course_name:
            raise ValueError("Course name must be provided")
        if course_name in self.courses:
            raise ValueError("Course already registered")
        self.courses.append(course_name)
        return list(self.courses)

    def drop_course(self, course_name):
        """
        Remove a course from the student's registration.

        Phrases: drop course, remove course, unregister course, delete course.

        Args:
            course_name: name of the course to remove.
        """
        if course_name not in self.courses:
            raise ValueError("Course not found")
        self.courses.remove(course_name)
        return list(self.courses)

    def list_courses(self):
        """
        Show all registered courses.

        Phrases: list courses, show courses, display courses, view courses, 
        see all courses, show me all courses, what courses do I have.

        """
        return list(self.courses)