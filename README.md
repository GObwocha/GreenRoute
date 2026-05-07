# GreenRoute
These are the Github Instructions on how to work on this project
Team Git Workflow: Feature Branching Guide
To ensure our backend, frontend, routing, and security code all integrate smoothly without overwriting each other's work, we are using a strict Feature Branch Workflow.

The Golden Rule: No one commits directly to the main branch. This includes the repository owner. We all work in our own isolated branches and merge them only when the code is tested and working.

Here is the step-by-step process we will all follow:

Phase 1: First-Time Setup (Do this only once)
1. Accept the GitHub Invitation
Before you can push any code, you must accept the collaborator invitation sent to your email by the repository owner.

2. Clone the Repository
Open your terminal, navigate to the folder where you want the project to live, and run:

Bash
git clone https://github.com/username/repo-name.git
(Replace the URL with our actual repository URL from GitHub).

3. Move into the Project Folder
You must move your terminal inside the newly created folder before running any other Git commands:

Bash
cd repo-name
⚠️ CRITICAL WARNING REGARDING BRANCHES ⚠️
If you created a local Git branch on your computer before running the git clone command, delete it or ignore it. That branch exists in a different Git universe and is not connected to our collaborative repository.

You must use the terminal to create your branch inside the cloned folder (see Step 4) so that it is properly linked to our team's project.

Phase 2: Creating Your Workspace (Do this for every new feature)
4. Create and Switch to Your Branch
Make sure your terminal is inside the cloned project folder. Create a new branch named after your role or the specific feature you are building. Use hyphens instead of spaces.

Bash
# Examples: 
# git checkout -b feature/frontend-ui
# git checkout -b feature/security-auth
# git checkout -b feature/routing-setup

git checkout -b feature/your-feature-name
You are now safely in your isolated workspace. You can start writing code!

Phase 3: Saving and Sharing Your Work
5. Save Your Progress (Commit)
As you write code and hit logical milestones, save your work locally:

Bash
# Stage all changes
git add . 

# Save a snapshot with a descriptive message
git commit -m "Brief description of what you built or fixed"
6. Send Your Code to GitHub (Push)
To back up your branch and make it visible to the rest of the team on GitHub:

Bash
# Run this the VERY FIRST time you push a new branch:
git push -u origin feature/your-feature-name

# For all future pushes on this branch, just run:
git push
Phase 4: Merging and Staying Updated
7. Create a Pull Request (PR)
When your feature is complete and working, go to our repository on GitHub.com. Click the "Compare & pull request" button next to your branch. This allows the team to review your code before it officially merges into the main branch.

8. Pull the Latest Code (Crucial!)
As other teammates finish their work and merge it into main, your local machine will fall behind. To see their updates (like the frontend developer needing to see the new backend API), you must regularly pull those changes into your branch:

Bash
# 1. Switch to your local main branch
git checkout main

# 2. Download the team's latest merged updates
git pull origin main

# 3. Switch back to your working branch
git checkout feature/your-feature-name

# 4. Merge the team's updates into your workspace
git merge main