<!-- Course: first needed for Stage 3 (alpha): a classmate has to reach your app
     without you in the room. See docs/course/DELIVERABLES.md -->

# Putting it online

Stage 3 requires a peer to set up and run your project on their own. Two ways to
pass that test: they run it locally from your README, or they open a URL. A URL
is better: fewer things go wrong, and you get feedback on the app instead of on
your install instructions.

Both options below are free.

---

## Web app hosting on Render.com

Render allows you to run an actual web server for free. 

1. Push your project to GitHub.
2. Connect Render to your Github account (see [Tutorial 05](https://github.com/CSCI-2521/tutorials/blob/main/tutorials/05-web-hosting-setup.md)).
3. Create a new "Web Service" on Render; if asked, choose "Python" as the type.
4. Connect that web service to your project's repo on Github
5. Render will automatically install and run your project, and will give you a URL that can be visited online. It redeploys itself every time you commit new code to to `main`.

**Requirements:** Your code 

---

## Other types of projects

If you have a project that is not a Web App, you must find another way for people to test it out. This could include letting them test it in person, or giving them instructions to install and run it locally.

---

## API keys

This is the part that goes wrong, so read it before your assistant writes code
that leaks a key into a public repo.

### Your assistant's key is not your app's key

The OpenRouter key you set up in week 1 belongs to **VS Code**, so that Kilo can
talk to a model while you work. It is not part of your project and never gets
committed. The one except to this is if you decide to make a web app that 
*talks to your inference provider* in order to build your app around an LLM.



### If your app itself calls an API

**On a server (Render):** it is possible to store a real secret, safely.
- Locally on your computer: put it in a file named `.env`. Be sure that you have a file in the repo named `.gitignore` in the repo that has the line `.env` in it. This will keep `git` from pushing your `.env` file to GitHub.com.
- Deployed: When you create a web service, Render has a section that allows you to copy and paste secrets into a specific file location on the server. You will then tell your coding agent where to look for that file when the app is deployed.

Another option is to **use an API that doesn't need a key.** Plenty are free and open. See [Tutorial 02](https://github.com/CSCI-2521/tutorials/blob/main/tutorials/02-project-brainstorming.md) for links to public free API services.

### If you leak a key anyway

It happens. Do this immediately, in this order:

1. **Revoke the key** at the provider's dashboard. Do this first; it is the only
   step that actually stops the damage.
2. Issue a new one.
3. Remove it from the code and commit.

Deleting the commit is not sufficient. Git keeps history, GitHub keeps forks, and
scrapers find public keys within minutes. Assume any key that reached a public
repo is compromised forever. Revoke or delete the key directly on the API provider's website.

GitHub scans public repos for known key formats and will usually block the push
before this can happen, but don't rely on it because it may not recognize every format.
