import pandas as pd


df = pd.read_csv('leetcode_username_form.csv')

usernames = df['LeetCode Username']

with open('students.txt', 'w') as file:
    file.write('\n'.join(usernames.values))

print('ok')