# Authentication Setup Guide

## 🎯 Overview
Your SkillForge AI app now has a complete authentication system with:
- ✅ User signup with email and username
- ✅ Secure password hashing (PBKDF2-HMAC-SHA256)
- ✅ Login with email or username
- ✅ Session management
- ✅ User profile in sidebar
- ✅ Logout functionality

## 📋 Setup Steps

### Step 1: Run the Authentication SQL Setup

1. Go to your Supabase dashboard: https://supabase.com
2. Open your project: `https://xmelhavwbkvdqnrolywc.supabase.co`
3. Click **SQL Editor** in the left sidebar
4. Copy the contents of `auth_setup.sql`
5. Paste into the SQL Editor
6. Click **Run**
7. You should see: "Success. No rows returned"

This creates:
- `users` table for authentication
- Security policies for row-level access
- Indexes for faster lookups
- Links `user_state` table to `users` table

### Step 2: Verify the Tables

1. In Supabase, click **Table Editor** (left sidebar)
2. You should see two tables:
   - ✅ `user_state` (existing)
   - ✅ `users` (new)

### Step 3: Test Your App

1. Activate your virtual environment:
   ```powershell
   & "D:\VS Code\Hackathon\.venv-3\Scripts\Activate.ps1"
   ```

2. Run the app:
   ```powershell
   streamlit run app.py
   ```

3. The app will now show a login/signup page first

## 🔐 How to Use

### For New Users:
1. Click the **"Sign Up"** tab
2. Enter your email, username, and password
3. Click **"✨ Sign Up"**
4. Switch to the **"Login"** tab
5. Enter your credentials and log in

### For Existing Users:
1. Enter your email or username
2. Enter your password
3. Click **"🔐 Login"**

### Logout:
- Look at the bottom of the sidebar
- You'll see your username and email
- Click **"🚪 Logout"** button

## 🔒 Security Features

- **Password Hashing**: Passwords are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salted Hashes**: Each password has a unique salt
- **Row-Level Security**: Supabase RLS policies protect user data
- **Session Management**: User state is maintained in Streamlit session
- **Input Validation**: Email, username, and password validation

## 📁 Files Created/Modified

### New Files:
- `auth_setup.sql` - SQL schema for users table
- `auth_ui.py` - Authentication UI components
- `AUTH_SETUP_GUIDE.md` - This file

### Modified Files:
- `supabase_client.py` - Added authentication functions
- `app.py` - Integrated authentication flow

## 🧪 Testing Checklist

- [ ] Run `auth_setup.sql` in Supabase
- [ ] Verify `users` table exists
- [ ] Start the app
- [ ] Create a test account
- [ ] Log in with the account
- [ ] Verify username shows in sidebar
- [ ] Test logout
- [ ] Test login again

## 🐛 Troubleshooting

### "Authentication is not available"
- Check that `supabase_client.py` can connect
- Verify `.streamlit/secrets.toml` has correct credentials

### "Email already exists" or "Username already exists"
- Try a different email or username
- Check the `users` table in Supabase to see existing accounts

### Can't log in
- Double-check your password
- Try using your username instead of email (or vice versa)
- Verify your account exists in the `users` table

### App shows blank page
- Check terminal for errors
- Ensure all dependencies are installed
- Try refreshing the browser (Ctrl+F5)

## 🎨 Customization

### Change Password Requirements:
Edit line in `supabase_client.py`:
```python
if len(password) < 6:  # Change 6 to your minimum
```

### Change Username Requirements:
Edit line in `auth_ui.py`:
```python
pattern = r'^[a-zA-Z0-9_]{3,20}$'  # Change 3-20 to your range
```

### Customize Login Page Style:
Edit the `render_auth_page()` function in `auth_ui.py`

## ✅ What's Next?

Your authentication system is ready! Users can now:
- Create accounts
- Log in securely
- Have personalized experiences
- Their data is saved per user account

The app will automatically load user-specific data from Supabase when they log in.

---

**Need help?** Re-run this guide or check the Supabase documentation at https://supabase.com/docs
