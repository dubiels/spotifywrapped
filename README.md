# Spotify Wrapped

## Overview

This README provides a description of each HTML page, folder structure, and instructions for running the Django project locally.

## Folder Structure

### `accounts`
- **Description:** Contains all the backend components.


### `static`
- **Description:** Includes static files like `styles.css`, `script.js`, or other images

### `templates`
- **Description:** Contains all HTML files used in the project.

### `spotifyWrapped`
- **Description:** The main application of the project. This is where the core functionality of the app is implemented.

## HTML Pages

### 1. `base.html`
- **Purpose**: Base layout for all pages with navigation, footer, and Dark Mode toggle.
- **Features**: Contains a header with navigation links that display the corresponding section when clicked

### 2. `dashboard.html`
- **Purpose**: Displays user-specific Spotify listening data.
- **Features**: Lists top Spotify tracks and integrates song previews.

### 3. `delete_account.html`
- **Purpose**: Allows users to delete their account.
- **Features**: Simple confirmation form for account deletion.

### 4. `followed_posts.html`
- **Purpose**: Shows Wrapped posts from users the current user follows.
- **Features**: Displays posts with like functionality and follower filtering.

### 5. `home.html`
- **Purpose**: Landing page for unauthenticated users.
- **Features**: Includes Spotify login button and basic app introduction.

### 6. `past_wraps.html`
- **Purpose**: Lists user's past Spotify Wrapped summaries.
- **Features**: Links to each Wrapped with timestamps for creation.

### 7. `wrap_detail.html`
- **Purpose**: Provides detailed view of a specific Spotify Wrapped.
- **Features**: Shows top tracks, artists, and albums for a particular Wrapped.


## User Story Summary and Completion Status

| User Story                                       | Frontend | Backend | Notes | Points |
|--------------------------------------------------|----------|---------|-------|---|
| Base User Story #1: Spotify API setup            |✅  | ✅ |  |  |
| Base User Story #2: User Authentication          | ✅ | ✅ |  |  |
| Base User Story #3: UI design                    |  |  |  |  |
| Base User Story #4: .gitignore setup             |✅  |✅  | Created✅ |  |
| Customizable User Story #5: Hear clips from top songs | ✅ | ✅ |  | +3 |
| Customizable User Story #8: View and interact with other users' Wrapped | |  |  | +9 |
| Customizable User Story #10: Dark mode |  |✅  | ✅ |  +2 |
| Customizable User Story #11: Share Wrapped on social media | ✅ | ✅ |  | +2 |
| Customizable User Story #13: Hosting on a service | ✅ | ✅ |  |+5  |
| Customizable User Story #14: Page transitions and hover effects |✅  |✅  |  | +2 |
| Customizable User Story #17: Figma file for the website | ✅ | ✅ |  |+1  |

## Deployment Guide

### 1. Install Dependencies

Install the required dependencies using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Instruction [here](https://docs.google.com/document/d/1feUq6mzyXzho7uwbJjj92cfXeNpSgE_8PkGePO1V3Z8/edit?usp=sharing)

### 3. Apply Migrations

Make migrations for the `accounts` app and apply them:

```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
```

### 4. Run the Development Server

Start the Django development server locally:

```bash
python manage.py runserver
```
