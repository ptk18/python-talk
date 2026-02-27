class CourseRegistration:
    def __init__(self, student_name, courses=None):
        self.student_name = student_name
        self.courses = list(courses) if courses else []

    def add_course(self, course_name):
        if not course_name:
            raise ValueError("Course name must be provided")
        if course_name in self.courses:
            raise ValueError("Course already registered")
        self.courses.append(course_name)
        return list(self.courses)

    def drop_course(self, course_name):
        if course_name not in self.courses:
            raise ValueError("Course not found")
        self.courses.remove(course_name)
        return list(self.courses)

    def list_courses(self):
        return list(self.courses)


def main():
    registration = CourseRegistration("Demo Student", ["Math 101"])
    print(f"Student: {registration.student_name}")
    print(f"Initial courses: {registration.list_courses()}")
    registration.add_course("History 201")
    print(f"After adding History 201: {registration.list_courses()}")
    registration.drop_course("Math 101")
    print(f"After dropping Math 101: {registration.list_courses()}")


if __name__ == "__main__":
    main()
