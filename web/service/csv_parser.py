import csv
from web.service.helper import get_numeric_id
from web.service.parsers import parse_phone_number
from web.models import Person, Student, StudyGroup, Department, EducationalOrganization, Subject, Teacher, Classroom
from datetime import date, time, datetime
from web.service.time_processing import get_week_day, parse_week_day, parse_datetime, TIME_FORMAT


DATE_FORMAT = '%d.%m.%Y'


def add_students_from_csv(path, edu_org=None, department=None):
    with open(path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        errors = []

        use_defined_department = True
        if department is None:
            use_defined = False

        use_defined_edu_org = True
        if edu_org is None:
            use_defined_edu_org = False

        for row in reader:
            success = True
            try:
                person = get_person(row)
                if person is None:
                    person = add_person(row)

                if not use_defined_department:
                    if not use_defined_edu_org:
                        edu_org = get_edu_org(row)
                    department = get_department(row, edu_org)

                student = person.student
                if student is None:
                    student = add_student(row, person, department)
                else:
                    if student.group.id != department.get_group_by_name(row['group_name']).id:
                        success = False
                        errors.append('Студент {student} уже записан, но в другую группу: {group}.'.format(
                            student = student.full_name(),
                            group = student.group.format_name()
                        ))
            except Exception as e:
                success = False
                errors.append('Ошибка при загрузке студента {student}. Сообщение об ошибке: "{error}"'.format(
                    student = '{} {} {}'.format(row['surname'], row['name'], row['father_name']),
                    error = '{}: {}'.format(e.__class__.__name__, e)
                ))
            if success:
                print(row['surname'], row['name'], row['father_name'])
        for e in errors:
            print(e)

def add_edu_org_structure_from_csv(path, edu_org=None):
    with open(path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        errors = []

        use_defined_edu_org = True
        if edu_org is None:
            use_defined_edu_org = False

        for row in reader:
            success = True
            try:
                if not use_defined_edu_org:
                    edu_org = get_edu_org(row)
                try:
                    department = get_department(row, edu_org)
                except ValueError:
                    department = add_department(row, edu_org)
                else:
                    success = False
                    errors.append('Подразделение "{}" в составе организации "{}" уже существует.'.format(row['department_name'], edu_org.name))
            except Exception as e:
                success = False
                errors.append('Ошибка при загрузке факультета "{department}". Сообщение об ошибке: "{error}"'.format(
                    department = '{} {}'.format(row['department_name'], row['department_short_name']),
                    error = '{}: {}'.format(e.__class__.__name__, e)
                ))
            if success:
                print(row['department_name'], row['department_short_name'], edu_org.short_name)
        for e in errors:
            print(e)

def add_groups_from_csv(path, department=None, edu_org=None):
    with open(path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        errors = []

        use_defined_department = True
        if department is None:
            use_defined = False

        use_defined_edu_org = True
        if edu_org is None:
            use_defined_edu_org = False

        for row in reader:
            success = True
            try:
                if not use_defined_department:
                    if not use_defined_edu_org:
                        edu_org = get_edu_org(row)
                    department = get_department(row, edu_org)
                try:
                    group = get_group(row, department)
                except ValueError:
                    group = add_group(row, department)
                else:
                    success = False
                    errors.append('Группа {} уже существует.'.format(row['group_name']))
            except Exception as e:
                success = False
                errors.append('Ошибка при загрузке группы {group}. Сообщение об ошибке: "{error}"'.format(
                    group = row['group_name'],
                    error = '{}: {}'.format(e.__class__.__name__, e)
                ))
            if success:
                print(row['group_name'], department.name)
        for e in errors:
            print(e)

def add_subjects_from_csv(path, department=None, edu_org=None):
    with open(path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        errors = []

        use_defined_department = True
        if department is None:
            use_defined_department = False

        use_defined_edu_org = True
        if edu_org is None:
            use_defined_edu_org = False

        for row in reader:
            success = True
            try:
                person = get_person(row)
                if person is None:
                    person = add_person(row)

                if not use_defined_department:
                    if not use_defined_edu_org:
                        edu_org = get_edu_org(row)
                    department = get_department(row, edu_org)

                teacher = person.teacher
                if teacher is None:
                    teacher = add_teacher(person, department)
                subject = get_subject(row, teacher)
                if subject is None:
                    subject = add_subject(row, teacher)
                else:
                    success = False
                    errors.append('Предмет {} у преподавателя {} уже существует.'.format(row['subject_name'], teacher.pd.full_name()))
            except Exception as e:
                success = False
                errors.append('Ошибка при загрузке предмета {subject}. Сообщение об ошибке: "{error}"'.format(
                    subject = row['subject_name'],
                    error = '{}: {}'.format(e.__class__.__name__, e)
                ))
            if success:
                print(row['subject_name'], teacher.pd.full_name())
        for e in errors:
            print(e)

def add_classrooms_from_csv(path, edu_org=None):
    with open(path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        errors = []

        use_defined_edu_org = True
        if edu_org is None:
            use_defined_edu_org = False

        for row in reader:
            success = True
            try:
                if not use_defined_edu_org:
                    edu_org = get_edu_org(row)

                classroom = get_classroom(row, edu_org)
                if classroom is None:
                    classroom = add_classroom(row, edu_org)
                else:
                    success = False
                    errors.append('Кабинет {} организации {} уже существует.'.format(
                        row['classroom_name'],
                        edu_org.name
                    ))
            except Exception as e:
                success = False
                errors.append('Ошибка при загрузке аудитории {classroom}. Сообщение об ошибке: "{error}"'.format(
                    classroom = row['classroom_name'],
                    error = '{}: {}'.format(e.__class__.__name__, e)
                ))
            if success:
                print(row['classroom_name'])
        for e in errors:
            print(e)

def add_person(row):
    birth_date = parse_datetime(row['birth_date'], DATE_FORMAT)
    if birth_date is not None:
        birth_date = birth_date.date()
    phone_number = parse_phone_number(row['phone_number'])
    if phone_number == '':
        phone_number = None
    email = row['email']
    if email == '':
        email = None
    person = Person(
        surname = row['surname'],
        name = row['name'],
        father_name = row['father_name'],
        birth_date = birth_date,
        vk_id = get_numeric_id(row['vk_id']),
        phone_number = phone_number,
        email = email
    )
    person.save()
    return person

def add_department(row, edu_org):
    department = Department(
        name = row['department_name'],
        short_name = row['department_short_name'],
        edu_org_id = edu_org.id
    )
    department.save()
    return department

def add_group(row, department):
    group = StudyGroup(
        name_format = row['group_name_format'],
        start_date = datetime.strptime(row['group_start_date'], DATE_FORMAT).date(),
        end_date = datetime.strptime(row['group_end_date'], DATE_FORMAT).date(),
        department_id = department.id
    )
    group.save()
    return group

def add_teacher(person, department):
    teacher = Teacher(
        person_id = person.id,
        department_id = department.id
    )
    teacher.save()
    return teacher

def add_subject(row, teacher):
    subject = Subject(
        name = row['subject_name'],
        short_name = row['subject_short_name'],
        teacher_id = teacher.person_id
    )
    subject.save()
    return subject

def add_student(row, person, department):
    student = Student(
        person_id = person.id,
        group_id = department.get_group_by_name(row['group_name']).id
    )
    student.save()
    return student

def add_classroom(row, edu_org):
    if row['classroom_number'] != '':
        classroom = Classroom(
            edu_org_id = edu_org.id,
            number_format = row['classroom_number_format'],
            number = str(row['classroom_number'])
        )
    else:
        classroom = Classroom(
            edu_org_id = edu_org.id,
            number_format = row['classroom_number_format']
        )
    classroom.save()
    return classroom

def get_edu_org(row):
    edu_org = EducationalOrganization.get(name=row['edu_org_name'])
    if edu_org is None:
        raise ValueError('No educational organization stated or such an educational organization do not exist')
    return edu_org

def get_department(row, edu_org):
    department = edu_org.get_department(name=row['department_name'])
    if department is None:
        raise ValueError('No department stated or such a department do not exist')
    return department

def get_group(row, department):
    group = department.get_group_by_name(row['group_name'])
    if group is None:
        raise ValueError('No group stated or such a group do not exist')
    return group

def get_subject(row, teacher):
    return teacher.get_subject(name=row['subject_name'])

def get_person(row):
    birth_date = parse_datetime(row['birth_date'], DATE_FORMAT)
    if birth_date is not None:
        birth_date = birth_date.date()
    return Person.get_by_match(
        surname = row['surname'],
        name = row['name'],
        father_name = row['father_name'],
        birth_date = birth_date,
        vk_id = get_numeric_id(row['vk_id']),
        phone_number = parse_phone_number(row['phone_number']),
        email = row['email']
    )

def get_classroom(row, edu_org):
    return edu_org.get_classroom(row['classroom_name'])
