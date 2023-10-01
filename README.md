# leetcode_student_evaluation

### Important!

Add your leetcode session to a file (you can retrieve that by inspecting the browser cookies "LEETCODE_SESSION")

### Parameters

--course [required=True]  
--term [required=True]  
--section [default='ALL']
--leetcode_session [default=os.path.join(_[PROJECT FOLDER]_, "leetcode_session")]  
--questions [required=True]  
--students [required=True]  
--check_form [default=False]  
--extract_usernames [default=False]  
--evaluate_students [default=False]  

Note that all steps are executed when all options (--check_form, --extract_usernames, --evaluate_students) are false 

### USAGE

pip install -r requirements.txt

E.g.:

python leetcode_student_evaluation.py --course CS1501 --term FALL23 --questions questions.txt --students students.txt

### INPUT

E.g.:  
[enrolled_students_email.txt](input/CS1501/FALL23/ALL/enrolled_students_email.txt) [(input/CS1501/FALL23/ALL/enrolled_students_email.txt)]  
[leetcode_username_form.csv](input/CS1501/FALL23/ALL/leetcode_username_form.csv) [(input/CS1501/FALL23/ALL/leetcode_username_form.csv)]  
[questions.txt](input/CS1501/FALL23/ALL/questions.txt) [(input/CS1501/FALL23/ALL/questions.txt)]  
[students.txt](input/CS1501/FALL23/ALL/students.txt) [(input/CS1501/FALL23/ALL/students.txt)]  

### OUTPUT

E.g.:  
[CS1501_FALL23_ALL_leetcode_evaluations.json](output/CS1501/FALL23/ALL/CS1501_FALL23_ALL_leetcode_evaluations.json) [(output/CS1501/FALL23/ALL/CS1501_FALL23_ALL_leetcode_evaluations.json)]  
[missing_students.txt](output/CS1501/FALL23/ALL/missing_students.txt) [(output/CS1501/FALL23/ALL/missing_students.txt)]  
[submission_fetch_error.txt](output/CS1501/FALL23/ALL/submission_fetch_error.txt) [(output/CS1501/FALL23/ALL/submission_fetch_error.txt)]  
[submission_not_found_error.txt](output/CS1501/FALL23/ALL/submission_not_found_error.txt) [(output/CS1501/FALL23/ALL/submission_not_found_error.txt)]  
[unknown_students.txt](output/CS1501/FALL23/ALL/unknown_students.txt) [(output/CS1501/FALL23/ALL/unknown_students.txt)]  
[unknown_username_error.txt](output/CS1501/FALL23/ALL/unknown_username_error.txt) [(output/CS1501/FALL23/ALL/unknown_username_error.txt)]  


CS1501_FALL23_ALL_leetcode_evaluations.json
```json
{
    "[LEETCODE_USERNAME]": {
        "best-time-to-buy-and-sell-stock": {
            "first_name": "[FIRST_NAME]",
            "last_name": "[LAST_NAME]",
            "pitt_username": "[PITT_USERNAME]",
            "question_id": "121",
            "status": "Accepted",
            "runtime": "210 ms",
            "memory": "97.3 MB",
            "total_correct": 211,
            "total_testcases": 211,
            "submitted_time_ago": "1\u00a0year, 9\u00a0months ago"
        }
    }
}
```
