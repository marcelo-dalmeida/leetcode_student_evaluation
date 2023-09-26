import warnings
import argparse
import collections
import json
import os
import re
from pathlib import Path

import requests
from ratelimiter import RateLimiter

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


rate_limiter = RateLimiter(max_calls=10, period=1)


def get_csrf_cookie(session_id: str) -> str:

    with rate_limiter:
        response = requests.get(
            "https://leetcode.com/",
            cookies={
                "LEETCODE_SESSION": session_id,
            },
        )

    return response.cookies["csrftoken"]


page_data_re = re.compile(r"<script>(?:(?!<script>).)*?var pageData = {.*?</script>", re.DOTALL)
page_data_content_re = re.compile("{.*}", re.DOTALL)
page_data_status_code_re = re.compile(r"parseInt\('(\d{2})', 10\)")


def get_question(question_name):

    query = """
        query questionTitle($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            titleSlug
            isPaidOnly
            difficulty
            likes
            dislikes
          }
        }
    """

    variables = {"titleSlug": question_name}

    request_json = {"query": query, "variables": variables}

    with rate_limiter:
        r = requests.post('https://leetcode.com/graphql/', json=request_json, headers=configuration)

    if r.status_code != 200:
        raise Exception(f"Failed to fetch question {question_name}; {r.status_code}, {r.reason}")

    response = r.json()

    return response['data']['question']


def get_recent_submissions(user, limit):

    query = """
        query recentAcSubmissions($username: String!, $limit: Int!) {
          recentAcSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
          }
        }
    """

    variables = {"username": user, "limit": limit}

    request_json = {"query": query, "variables": variables}

    with rate_limiter:
        r = requests.post('https://leetcode.com/graphql/', json=request_json, headers=configuration)

    if r.status_code != 200:
        raise Exception(f"Failed to fetch submissions from {user}; {r.status_code}, {r.reason}")

    response = r.json()

    return response['data']['recentAcSubmissionList']


def get_submission_details(submission_id):
    # json5 supports parsing javascript objects
    import json5

    with rate_limiter:
        r = requests.get(f'https://leetcode.com/submissions/detail/{submission_id}', cookies=configuration)

    if r.status_code != 200:
        raise Exception(f"Failed to fetch submission {submission_id}; {r.status_code}, {r.reason}")

    try:

        response_text = r.text

        # We need to parse directly from the html
        # Using re because the information is inside one of many <script> tags
        page_data = re.search(page_data_re, response_text).group()

        # Getting the actual javascript object
        page_data_content = re.search(page_data_content_re, page_data).group()

        # Fixing status code
        page_data_content = re.sub(page_data_status_code_re, r'\1', page_data_content)

        data = json5.loads(page_data_content)

        status_codes = {
            10: "Accepted",
            11: "Wrong Answer",
            12: "Memory Limit Exceeded",
            13: "Output Limit Exceeded",
            14: "Time Limit Exceeded",
            15: "Runtime Error",
            16: "Internal Error",
            20: "Compile Error",
            21: "Unknown Error",
            30: "Timeout"
        }

        data['submissionData']['status'] = status_codes[data['submissionData']['status_code']]

    except AttributeError:
        warnings.warn(f"Couldn't fetch details for submission {submission_id}")
        return None

    return data


if __name__ == "__main__":

    # parsing command line arguments
    parser = argparse.ArgumentParser(
        prog='simulation',
        description='Run the simulation, replay, summary, analysis...')

    parser.add_argument('--course', default="CS1501")
    parser.add_argument('--term', required=True)
    parser.add_argument('--section', required=True)
    parser.add_argument('--leetcode_session', default=os.path.join(ROOT_DIR, "leetcode_session"))
    parser.add_argument('--questions', required=True)
    parser.add_argument('--students', required=True)
    args = parser.parse_args()

    path = f"./output/{args.course}/{args.term}/{args.section}"
    Path(path).mkdir(parents=True, exist_ok=True)

    # reading questions
    with open(args.questions, 'r') as file:
        questions = file.read().splitlines()

    # reading students
    with open(args.students, 'r') as file:
        students = file.read().splitlines()

    # Get the next two values from your browser cookies
    with open(args.leetcode_session, 'r') as file:
        leetcode_session = file.read()
    csrf_token = get_csrf_cookie(leetcode_session)

    configuration = {
        "x-csrftoken": csrf_token,
        "csrftoken": csrf_token,
        "LEETCODE_SESSION": leetcode_session,
        "Referer": "https://leetcode.com"
    }

    ###  PROCESSING EVALUATIONS  ###

    # Getting question ids
    question_ids = {}
    for question_name in questions:
        question = get_question(question_name)
        question_id = question['questionId']
        question_ids[question_name] = question_id

    # Getting student recent submissions
    unknown_username = set()
    submission_not_found = set()
    student_submissions = {}
    for student in students:

        student = student.strip()

        print(f'Checking submissions id for username {student}')

        recent_submissions = get_recent_submissions(student, 30)

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

    submission_fetch_error = set()
    # Getting student submissions' details
    student_evaluation = collections.defaultdict(dict)
    for student, submissions in student_submissions.items():

        for submission_id, question_name in submissions:
            data = get_submission_details(submission_id)

            if data is None:
                submission_fetch_error.add(f"{student}\t{submission_id}")
                continue

            print(f'Getting submissions for username {student}')

            question_id = question_ids[question_name]

            assert question_id == data['questionId']

            evaluation = {
                'question_id': data['questionId'],
                'status': data['submissionData']['status'],
                'runtime': data['submissionData']['runtime'],
                'memory': data['submissionData']['memory'],
                'total_correct': int(data['submissionData']['total_correct']),
                'total_testcases': int(data['submissionData']['total_testcases'])
            }

            student_evaluation[student][question_name] = evaluation

    with open(os.path.join(path, 'submission_fetch_error.txt'), 'w') as file:
        file.write('\n'.join(list(submission_fetch_error)))

    # Saving all information
    with open(os.path.join(path, f"{args.course}_{args.term}_{args.section}_leetcode_evaluations.json"), 'w') as file:
        json.dump(student_evaluation, file, indent=4)
