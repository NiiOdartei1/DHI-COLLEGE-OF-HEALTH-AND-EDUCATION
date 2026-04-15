# Render.com Deployment Guide for DHI College LMS

## Overview
This guide will help you deploy the DHI College of Health and Education LMS to Render.com.

## Prerequisites
- A Render.com account (free tier available)
- GitHub repository with the project code
- Gmail account for email functionality (optional)

## Deployment Steps

### 1. Prepare Your Repository
Ensure your repository contains:
- `requirements.txt` (production dependencies)
- `render.yaml` (Render configuration)
- `.env.example` (environment variables template)
- `app.py` (Flask application)
- `config.py` (configuration)

### 2. Push to GitHub
Make sure your code is pushed to GitHub:
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 3. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up or log in
3. Connect your GitHub account

### 4. Create PostgreSQL Database
1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Configure:
   - Name: `dhi-lms-db`
   - Database: `dhi_lms`
   - User: `dhi_lms_user`
   - Region: Choose nearest to your users
   - Plan: Free tier (or paid for production)
4. Click "Create Database"
5. Save the **Database Internal Database URL** from the dashboard

### 5. Create Web Service
1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Review the configuration:
   - Name: `dhi-lms`
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`
6. Click "Create Web Service"

### 6. Configure Environment Variables
In your web service settings, add the following environment variables:

#### Required Variables
- `FLASK_ENV`: `production`
- `SECRET_KEY`: Generate a secure random key (Render can auto-generate this)
- `RENDER_DISK_PATH`: `/opt/render/project/uploads`
- `DATABASE_URL`: Automatically set by Render (linked to your PostgreSQL database)

#### Email Configuration (Optional)
- `MAIL_USERNAME`: Your Gmail address
- `MAIL_PASSWORD`: Gmail App Password (create one at https://myaccount.google.com/apppasswords)

#### Zoom Integration (Optional)
- `ZOOM_ACCOUNT_ID`: Your Zoom account ID
- `ZOOM_ACCOUNT_EMAIL`: Your Zoom email
- `ZOOM_CLIENT_ID`: Your Zoom client ID
- `ZOOM_CLIENT_SECRET`: Your Zoom client secret

### 7. Configure Persistent Disk
The `render.yaml` already includes a 10GB persistent disk configuration:
- Mount path: `/opt/render/project/uploads`
- Used for: File uploads, receipts, profile pictures, etc.

### 8. Deploy
1. Render will automatically build and deploy your application
2. Monitor the build logs in the Render dashboard
3. Once deployed, you'll receive a public URL (e.g., `https://dhi-lms.onrender.com`)

### 9. Initialize Database
The application automatically runs `one_time_init()` on startup, which:
- Creates all database tables
- Creates a default SuperAdmin account:
  - Username: `SuperAdmin`
  - Password: `Password123`
  - Email: `superadmin@dhi.edu.gh`

**Important:** Change the SuperAdmin password immediately after first login!

### 10. Access Your Application
- Visit your Render URL (e.g., `https://dhi-lms.onrender.com`)
- Login as SuperAdmin to configure the system
- Set up programmes, levels, and other initial data

## Post-Deployment Configuration

### Email Setup (Recommended)
1. Create a Gmail App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification
   - App Passwords > Generate
   - Use a descriptive name (e.g., "DHI LMS")
2. Add the app password to `MAIL_PASSWORD` environment variable
3. Test email functionality

### Custom Domain (Optional)
1. Purchase a domain (e.g., `dhi.edu.gh`)
2. In Render dashboard, go to your web service > Settings > Custom Domains
3. Add your domain and follow DNS instructions

### SSL/HTTPS
Render automatically provides SSL certificates for all deployments.

## Monitoring and Logs

### View Logs
- Go to your web service in Render dashboard
- Click "Logs" tab
- View real-time application logs

### Database Access
- Go to your PostgreSQL database in Render dashboard
- Use the "Internal Database URL" to connect externally
- Or use Render's built-in PostgreSQL interface

## Troubleshooting

### Build Failures
- Check the build logs in Render dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version compatibility (Python 3.11)

### Database Connection Issues
- Verify `DATABASE_URL` environment variable is set
- Check PostgreSQL database is running
- Ensure database credentials are correct

### File Upload Issues
- Verify persistent disk is mounted correctly
- Check `RENDER_DISK_PATH` environment variable
- Ensure folder permissions are correct

### Email Not Sending
- Verify Gmail credentials are correct
- Check if 2-Step Verification is enabled
- Ensure App Password is used (not regular password)

## Scaling

### Vertical Scaling
- Upgrade your web service plan for more CPU/RAM
- Upgrade PostgreSQL plan for better performance

### Horizontal Scaling
- Add more instances to your web service
- Consider load balancing for high traffic

## Security Recommendations

1. **Change Default Passwords**: Change SuperAdmin password immediately
2. **Use Strong SECRET_KEY**: Generate a secure random key
3. **Enable HTTPS**: Render provides this automatically
4. **Regular Backups**: Render automatically backs up PostgreSQL
5. **Monitor Logs**: Regularly check for suspicious activity
6. **Keep Dependencies Updated**: Regularly update `requirements.txt`

## Cost Considerations

### Free Tier Limits
- Web Service: 750 hours/month (limited CPU/RAM)
- PostgreSQL: 90 days free, then $7/month
- Persistent Disk: 10GB included

### Production Recommendations
- Upgrade to paid plans for better performance
- Consider separate database instance for production
- Monitor usage and scale as needed

## Support

For issues specific to:
- **Render.com**: Visit [Render Documentation](https://render.com/docs)
- **Application**: Check application logs or contact development team

## Notes

- File uploads are stored on Render's persistent disk (10GB included)
- The application uses Socket.IO for real-time features (chat, notifications)
- PDF generation requires WeasyPrint (included in requirements.txt)
- The application automatically handles database migrations on startup
