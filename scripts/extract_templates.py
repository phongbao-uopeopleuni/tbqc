import os
import re

file_path = 'd:/tbqc/admin_routes.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Extract templates
def extract_template(name):
    # Matches `NAME = '''...'''` or `NAME = """..."""`
    pattern = re.compile(f'{name}\\s*=\\s*(?:\'\'\'(.*?)\'\'\'|"""(.*?)""")', re.DOTALL)
    match = pattern.search(content)
    if match:
        return match.group(1) if match.group(1) is not None else match.group(2)
    return None

login_tpl = extract_template('ADMIN_LOGIN_TEMPLATE')
dash_tpl = extract_template('ADMIN_DASHBOARD_TEMPLATE')
users_tpl = extract_template('ADMIN_USERS_TEMPLATE')
data_tpl = extract_template('DATA_MANAGEMENT_TEMPLATE')

os.makedirs('d:/tbqc/templates/admin', exist_ok=True)

if login_tpl:
    with open('d:/tbqc/templates/admin/login.html', 'w', encoding='utf-8') as f:
        f.write(login_tpl.strip())
        
if dash_tpl:
    with open('d:/tbqc/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dash_tpl.strip())

if users_tpl:
    with open('d:/tbqc/templates/admin/users.html', 'w', encoding='utf-8') as f:
        f.write(users_tpl.strip())

if data_tpl:
    with open('d:/tbqc/templates/admin/data_management.html', 'w', encoding='utf-8') as f:
        f.write(data_tpl.strip())

# Create a placeholder for requests
with open('d:/tbqc/templates/admin/requests.html', 'w', encoding='utf-8') as f:
    f.write('<h1>Admin Requests</h1><p>Template placeholder</p>')

# 2. Modify render functions
new_content = content.replace("render_template_string(ADMIN_LOGIN_TEMPLATE", "render_template('admin/login.html'")
new_content = new_content.replace("render_template_string(ADMIN_REQUESTS_TEMPLATE", "render_template('admin/requests.html'")
new_content = new_content.replace("render_template_string(ADMIN_USERS_TEMPLATE", "render_template('admin/users.html'")

# 3. Remove template string definitions at the bottom
cut_index = new_content.find('ADMIN_LOGIN_TEMPLATE = ')
if cut_index != -1:
    comment_idx = new_content.rfind('# Templates', 0, cut_index)
    if comment_idx != -1 and (cut_index - comment_idx) < 50:
        cut_index = comment_idx
    new_content = new_content[:cut_index]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done extraction and modification!')
