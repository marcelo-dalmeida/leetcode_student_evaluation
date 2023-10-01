import re
import warnings

import requests
from ratelimiter import RateLimiter


rate_limiter = RateLimiter(max_calls=10, period=1)

page_data_re = re.compile(r"<script>(?:(?!<script>).)*?var pageData = {.*?</script>", re.DOTALL)
page_data_content_re = re.compile("{.*}", re.DOTALL)
page_data_status_code_re = re.compile(r"parseInt\('(\d{2})', 10\)")
submitted_time_re = re.compile(r'.*<div id="submitted-time">Submitted: <strong><span id="result_date">.*</span></strong></div>')


def get_csrf_cookie(session_id):

    with rate_limiter:
        response = requests.get(
            "https://leetcode.com/",
            cookies={
                "LEETCODE_SESSION": session_id,
            },
        )

    return response.cookies["csrftoken"]


def get_configuration(leetcode_session):

    csrf_token = get_csrf_cookie(leetcode_session)

    configuration = {
        "x-csrftoken": csrf_token,
        "csrftoken": csrf_token,
        "LEETCODE_SESSION": leetcode_session,
        "Referer": "https://leetcode.com"
    }

    return configuration


def get_question(question_name, configuration):

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


def get_recent_submissions(user, limit, configuration):

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


def get_submission_details(submission_id, configuration):
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

        submitted_time = re.search(submitted_time_re, response_text).group()

        submitted_time = (submitted_time.strip()
                          .replace('<div id="submitted-time">Submitted: <strong><span id="result_date">', '')
                          .replace('</span></strong></div>', ''))

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
        data['submissionData']['submitted_time_ago'] = submitted_time

    except AttributeError:
        warnings.warn(f"Couldn't fetch details for submission {submission_id}")
        return None

    return data
