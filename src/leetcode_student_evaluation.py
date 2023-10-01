import argparse
import warnings
import collections
import json
import os
from pathlib import Path

import pandas as pd

import leetcode_utils

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


def check_form_submissions(form_info, base_path):

    with open(f'../input/{base_path}/enrolled_students_email.txt', 'r') as file:
        emails = file.read().splitlines()

    pitt_usernames = [email.split('@')[0].strip().lower() for email in emails]

    reported_pitt_usernames = set(
        [pitt_username.split('@')[0].strip() for pitt_username in form_info['Pitt Username']]
    )

    unknown_pitt_username = []
    for reported_pitt_username in reported_pitt_usernames:
        if reported_pitt_username not in pitt_usernames:
            unknown_pitt_username.append(reported_pitt_username)

    pitt_usernames = set(pitt_usernames)

    missing_students = []
    for pitt_username in pitt_usernames:
        if pitt_username not in reported_pitt_usernames:
            missing_students.append(pitt_username)

    with open(f'../output/{base_path}/unknown_students.txt', 'w') as file:
        file.write('\n'.join(unknown_pitt_username))

    missing_students = [f"{missing_student}@pitt.edu" for missing_student in missing_students]

    with open(f'../output/{base_path}/missing_students.txt', 'w') as file:
        file.write('\n'.join(missing_students))


def extract_leetcode_usernames(form_info, base_path):

    form_info = form_info.sort_values(by=['Last Name', 'First Name'])
    usernames = form_info['LeetCode Username']

    with open(f'../input/{base_path}/SECTEST_students.txt', 'w') as file:
        file.write('\n'.join(usernames.values))


def evaluate_leetcode_students(questions, students, form_info, leetcode_session, base_path):

    configuration = leetcode_utils.get_configuration(leetcode_session)

    # Getting question ids
    question_ids = {}
    for question_name in questions:
        question = leetcode_utils.get_question(question_name, configuration)
        question_id = question['questionId']
        question_ids[question_name] = question_id

    # Getting student recent submissions
    unknown_username = set()
    submission_not_found = set()
    student_submissions = {}
    for student in students:

        student = student.strip()

        print(f'Checking submissions id for username {student}')

        recent_submissions = leetcode_utils.get_recent_submissions(student, 30, configuration)

        if recent_submissions is None:
            unknown_username.add(student)
            warnings.warn(f'Skipping username {student}. Not Found')
            continue

        student_submissions[student] = [(submission['id'], submission['titleSlug']) for submission in recent_submissions
                                        if submission['titleSlug'] in questions]

        student_submitted_questions = [question_name for _, question_name in student_submissions[student]]

        for question_name in questions:
            if question_name not in student_submitted_questions:
                submission_not_found.add(f"{student}\t{question_name}")

    with open(os.path.join(path, 'unknown_username_error.txt'), 'w') as file:
        file.write('\n'.join(list(unknown_username)))

    with open(os.path.join(path, 'submission_not_found_error.txt'), 'w') as file:
        file.write('\n'.join(list(submission_not_found)))

    # Getting student submissions' details
    submission_fetch_error = set()
    student_evaluation = collections.defaultdict(dict)
    for student, submissions in student_submissions.items():

        for submission_id, question_name in submissions:
            data = leetcode_utils.get_submission_details(submission_id, configuration)

            if data is None:
                submission_fetch_error.add(f"{student}\t{submission_id}")
                continue

            print(f'Getting submissions for username {student}')

            question_id = question_ids[question_name]

            assert question_id == data['questionId']

            student_info = form_info[form_info['LeetCode Username'] == student]

            evaluation = {
                'first_name': student_info['First Name'].values[0],
                'last_name': student_info['Last Name'].values[0],
                'pitt_username': student_info['Pitt Username'].values[0],
                'question_id': data['questionId'],
                'status': data['submissionData']['status'],
                'runtime': data['submissionData']['runtime'],
                'memory': data['submissionData']['memory'],
                'total_correct': int(data['submissionData']['total_correct']),
                'total_testcases': int(data['submissionData']['total_testcases']),
                'submitted_time_ago': data['submissionData']['submitted_time_ago']
            }

            student_evaluation[student][question_name] = evaluation

    with open(os.path.join(path, 'submission_fetch_error.txt'), 'w') as file:
        file.write('\n'.join(list(submission_fetch_error)))

    # Saving all information
    with open(os.path.join(path, f"{base_path.replace('/', '_')}_leetcode_evaluations.json"), 'w') as file:
        json.dump(student_evaluation, file, indent=4)


if __name__ == "__main__":

    # parsing command line arguments
    parser = argparse.ArgumentParser(
        prog='LeetCode Evaluation',
        description='Evaluate Students on LeetCode problems')

    parser.add_argument('--course', required=True)
    parser.add_argument('--term', required=True)
    parser.add_argument('--section', default="ALL")
    parser.add_argument('--leetcode_session', default=os.path.join(ROOT_DIR, "../leetcode_session"))
    parser.add_argument('--questions', required=True)
    parser.add_argument('--students', required=True)
    parser.add_argument('--check_form', action='store_true')
    parser.add_argument('--extract_usernames', action='store_true')
    parser.add_argument('--evaluate_students', action='store_true')
    args = parser.parse_args()

    base_path = f"{args.course}/{args.term}/{args.section}"

    args.questions = f"../input/{base_path}/{args.questions}"
    args.students = f"../input/{base_path}/{args.students}"

    form_info = pd.read_csv(f'../input/{base_path}/leetcode_username_form.csv')
    form_info['First Name'] = form_info['First Name'].str.strip()
    form_info['Last Name'] = form_info['Last Name'].str.strip()
    form_info['Pitt Username'] = form_info['Pitt Username (e.g., aaa123)'].str.strip().lower()
    form_info['LeetCode Username'] = form_info['LeetCode Username'].str.strip()
    form_info.drop(['Pitt Username (e.g., aaa123)'], inplace=True)

    path = f"../output/{base_path}"
    Path(path).mkdir(parents=True, exist_ok=True)

    if not args.check_form and not args.extract_usernames and not args.evaluate_students:
        args.check_form = True
        args.extract_usernames = True
        args.evaluate_students = True

    if args.check_form:
        check_form_submissions(form_info, base_path)
    if args.extract_usernames:
        extract_leetcode_usernames(form_info, base_path)
    if args.evaluate_students:

        with open(args.questions, 'r') as file:
            questions = file.read().splitlines()

        with open(args.students, 'r') as file:
            students = file.read().splitlines()

        with open(args.leetcode_session, 'r') as file:
            leetcode_session = file.read()

        evaluate_leetcode_students(questions, students, form_info, leetcode_session, base_path)
