# leetcode_student_evaluation

### Important!

Add your leetcode session to a file (you can retrieve that by inspecting the browser cookies "LEETCODE_SESSION")

### Parameters

--course [default="CS1501"]  
--term [required=True]  
--section [required=True]  
--leetcode_session [default=os.path.join(_[PROJECT FOLDER]_, "leetcode_session")]  
--questions [required=True]  
--students [required=True]  

### USAGE

pip install -r requirements.txt

E.g.:

python leetcode_student_evaluation.py --term FALL23 --section 1060 --questions TEST_questions.txt --students SECTEST_students.txt

### OUTPUT

E.g.:

```json
{
    "neal_wu": {
        "best-time-to-buy-and-sell-stock": {
            "question_id": "121",
            "status": "Accepted",
            "runtime": "210 ms",
            "memory": "97.3 MB",
            "total_correct": 211,
            "total_testcases": 211
        }
    }
}
```
