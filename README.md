🚀 FastAPI OAuth2 Auth App with Email Verification & Social Login
A secure, full-featured FastAPI authentication service with:

OAuth2 (JWT)

Email verification

Password reset via email

Google & GitHub OAuth login

MySQL database

Role-based access control (Admin/User)

Jinja2-powered HTML pages

## 🔒 Project Screenshots

![HTML Screen](images/image.png)
![Swagger Screen](images/image_2.png)
![Authorization Complete](images/image_3.png)
		

✨ Features
🔐 JWT Authentication with OAuth2 password flow

📧 Email verification link sent on registration

🔑 Password reset functionality

🌐 Login with Google or GitHub

🗄 MySQL database integration

🧑‍💻 Role-based routes (Admin / User)

🎨 HTML templates using Jinja2

📜 Swagger/OpenAPI docs included

🛡 Secure password hashing with Passlib

🏁 Getting Started
1️⃣ Clone the repository
bash
Copy
Edit
git clone https://github.com/SujayKumarMondal/FastAPI-OAuth2.git
cd FastAPI-OAuth2
2️⃣ Create & activate virtual environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
3️⃣ Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
4️⃣ Configure environment variables
Create a .env file in the project root:

env
Copy
Edit
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/fastapi_auth
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
🗄 MySQL Setup
Run in MySQL Workbench:

sql
Copy
Edit
CREATE DATABASE fastapi_auth;
SQLAlchemy models will auto-create required tables on first run.

▶ Run the App
bash
Copy
Edit
uvicorn main:app --host 0.0.0.0 --port 7003 --reload
Access:

Homepage: http://localhost:7003/

Swagger UI: http://localhost:7003/docs

🔐 Authentication Flow
Registration
POST /register → Create user, send verification email with token.

GET /verify-email?token=... → Mark user as verified.

Login
Username/password: POST /login → Returns JWT access token.

Google OAuth: GET /auth/google

GitHub OAuth: GET /auth/github

Password Reset
POST /forgot-password → Send reset token via email.

POST /reset-password → Reset password using token.

Role-based Access
Admin routes: Require is_admin=True in DB.

User routes: Any authenticated & verified user.

📄 API Endpoints
Method	Endpoint	Description	Auth Required
POST	/register	Register a new user	No
GET	/verify-email	Verify email using token	No
POST	/login	Login with username/password	No
GET	/auth/google	Login with Google	No
GET	/auth/github	Login with GitHub	No
POST	/forgot-password	Send password reset link	No
POST	/reset-password	Reset password	No
GET	/users/me	Get current user profile	Yes
GET	/admin/dashboard	Admin dashboard stats	Admin only

🌐 Homepage
Displays project info, links to Swagger UI, GitHub, and LinkedIn.

Footer dynamically shows the current year.

📜 License
Licensed under the MIT License. See LICENSE for details.

🔗 Author Links
💼 LinkedIn

🔗 GitHub

If you want, I can also add example Swagger request/response payloads for every endpoint in this README so people know exactly how to use your API without guessing. That would make it even more developer-friendly.