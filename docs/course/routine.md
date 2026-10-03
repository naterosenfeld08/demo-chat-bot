# The routine

Every feature goes through the same steps.

The grade is not "does the app work." The grade is evidence that you ran the
routine, and that evidence accumulates on GitHub by itself as you work.

These are the steps we discussed in class:

<img width="1721" height="981" alt="image" src="https://github.com/user-attachments/assets/639cc139-4a9f-4ae1-8cd2-66573d9d7358" />

### Outline of steps
1. Design
- You write a user storiy (“As a _______, I can _______”)...
- Keep the change small! Agents lose focus on big tasks.

2. Spec
- Agent 1 drafts spec
- Optionally have Agent 2 (different AI model!) review it
- You discuss, request modifications, and approve it

3. Write the tests first
- Agent 1 writes a plan and the tests for it *before* building the feature/fixing the bug
- These tests fail (obviously)
- Agent 2 describes each test to you in plain English
- Agent 2 compares the tests to the spec
- You decide what needs to be fixed/added
- Agent 1 fixes the tests
- Repeat until you and Agent 2 are satisfied

4. Build
- Agent 1 builds the feature/fixes the bug
- Tests pass
- Agent 2 reviews the code
- Read the review and discuss with Agent 2 to decide what needs to be fixed. 
- Optionally get a second opinion from Agent 3 using a different third AI model.
- Issues? Back to Step 3: share the code review and request fixes from Agent 1.
- Repeat steps 3 and 4 until no major issues found in code review.

5. Real user tests
- Bug? --> Back to Step 3
- Spec was wrong? --> Back to Step 2
- Design was wrong? --> Back to Step 1
- All good? Do it again!

Use a different chat or model for each role where you can. A model that wrote
something is usually a bad judge of it. It will defend its own work, and it will
overlook exactly what it overlooked the first time.

---
As you work through these steps, you will be synchronizing your code on your computer with the code on Github. The two main steps you will take during this are known as *commits* and *pull requests*:

**Commit**. A snapshot of your project at one point in time, plus a message saying what changed and why. Every commit gets a unique ID, so you can always go back to it. Think of it as a saved checkpoint: instead of "final_v2_really_final.doc", you have a chain of snapshots, each labeled "added the failing tests" or "fixed the login bug". A commit records the difference from the previous one, not the whole project over again.

**Pull request** (PR). A proposal to merge one set of commits (usually on a branch) into another branch. In our case it will be your main branch. It's called a "pull" request because you're asking the code maintainers (you are the maintainer here) to pull your work in. The PR page shows the full set of differences or changes and usually runs automated tests. You can also leave a "comment" on a PR, and we will use this to post code reviews when we get them.  No code every gets merged into the project until someone approves it, so having a PR doubles as both a gate and a record of the discussion.

**Branch**: A temporary copy of your code where you can make changes without affecting the actual running code on the repo until you are ready. The main running code is on its own branch, called *main*.

**Worktree**: a separate folder on your computer, where the agent and you can work on your code without affecting the main copy of the code that you have. Each **worktree** will contain its own **branch**.

In your classroom workflow, commits and pull requests fit together like this: each commit is one checkpoint on the way to a feature, and the pull request is the container that holds the whole chain, plus the spec, the failing tests, the code review, and the builder's replies, all in one place. So one task or feature is usually one _PR_, and it may have many *commits* in it.

## The commits, pull requests, and comments expected

Note: Here is when to ask agents to make a *pull request* (PR), when to make a commit, when to post a comment on a PR, and when to mark the PR ready for review.

- Commit 1: the initial spec written by the agent. Ask Agent 1 top open a "draft" *pull request* at this point. 
- Commit 2: final revised spec and a log at the bottom of the spec including questions and answers from your discussion with agent 2. 
- Commit 3: the failing tests (end of step 3). This is before you review the tests with agent 2.
- Commit 4: Ask agent 2 to post a comment on the draft PR showing the review outcome including any responses from you. Then Agent 1 will commit the revised tests.
- Commit 4.1, 4.2, ...: Other commits here, optionally: if there are multiple rounds of revision of the tests, you can have agent 1 commit each of them and add to the log file showing the issues raised and your responses and the changes made. These commits and the logs are evidence of your iterating the code review process. 
- Commit 5.1, 5.2, ...: the initial build. Agent 1 can keep making commits as the feature takes shape.
- Comments posted on the PR: Ask Agent 2 to post their comments on the PR along with your responses.
- Commit 6.1, 6.2, ... Agent 1 fixes issues found in code review in response to the comments;
- Additional comments, optionally: If you have several rounds of code review, have Agent 2 post the new issues (and any responses from you) as another comment on the PR. These comments and the subsequent changes are evidence of your iterating the code review process. 
- Finally, Agent 1 marks the PR "ready for review" (instead of "draft") once every test passes locally. That's when GitHub runs the suite, and when code review starts.

## Getting updates
---

## 0. Open a new branch in a new worktree, check for updates from Instructor
We never want to do work directly on the main code in the repo. Instead, we will always open a new "branch". 

Before you start work, ask your agent:

```
Please make sure you are on a new branch, and that you were working in a separate worktree on this computer. Please tell me the name of the branch, tell me where to find the worktree on my computer, and give me a link to the work tree.
```

Then ask your agent to check for udpates to this template from the instructor:
```
git remote add upstream https://github.com/CSCI-2521/project-template
git fetch upstream
git merge upstream/main
git push
```

## 1. Design
This is where you describe the feature you want to build. These features will be listed in your [`docs/backlog.md`](../../docs/backlog.md) document.

## 2. Write the spec
Copy [`specs/TEMPLATE.md`](../../specs/TEMPLATE.md) to `specs/NN-yourfeaturename.md`, where
`NN` is the backlog number from your [`docs/backlog.md`](../../docs/backlog.md) document. Have an AI expand the backlog story into a full specification document:
what it does, what it does **not** do, and what done means (the "acceptance criteria").

The "does not do" section is one people sometimes skip.
Without it an assistant may cheerfully build three features you didn't ask for.

Then ask Agent 1 to commit the spec, and to "open a "draft" *pull request*" at this point. This will track all of your work on the feature and will be the main thing that is graded:

```
Expand the backlog story in specs/02-yourfeaturename.md into a full specification document:
what it does, what it does **not** do, and what done means (the "acceptance criteria").

When you are done, commit the spec, and open a *draft* pull request to track this work.
```

### Question round

Bring in a **different** AI model (Agent 2). Its only job is to find what your spec forgot:

```
Read this feature spec and the user story in docs/backlog.md. Do not write code and do not implement anything. Ask me
at most 10 questions about what it fails to specify: edge cases, empty inputs,
errors, things done twice, things done in the wrong order, hostile input. Most
important first.
```

### Post the feedback as a comment on the PR. 

After your discussion with Agent 2, answer any questions it has and then have it post a comment on the PR:

```
Post this feedback and my answers as a comment on the draft PR
```

### Give test review back to Agent 1

Give the questions and your answers back to Agent 1.


```
Please read the new comment on the PR. Then revise the spec accordingly, and include any questions and answers in the comment at the bottom of the spec in a brief
log so they don't get asked again by an AI that shows up later with no
memory of this conversation.

When you are done, commit the new spec to the PR.
```

## 3. Tests before building

Ask agent 1 to write tests for the spec.

```
We are going to use test-driven development. 

Please write tests in `tests/`, at least one for each line of the acceptance criteria in the spec, and run them. 

Every test should run but then fail because the feature doesn't exist yet. 

Then commit the tests to the PR.
```

### Question round

Bring in a **different** AI model (Agent 2). Its only job is to review the tests and compare them to the spec. Give them a prompt like this:

```
Read specs/NN-yourfeaturename.md in full, including the question log at the bottom, and every file in tests/. Do not write, edit, or fix any code. Run the test suite and record what each test actually does.

    First: one line per test naming and describing the test in plain English. Say what a user would have to do to hit this case, and exactly what the test accepts as success. Do not use code words, jargon, or function names. If you cannot describe a test this way, say so.

    Then: a coverage table. One row per line of the acceptance criteria in the spec, and each row lists the test that covers it, or says MISSING.

    Then: findings in four lists, most important first, 10 items total or fewer.

        Missing: an acceptance-criteria line, edge case, error case, or "does not do" rule from the spec that has no test. Name the spec line.
        Wrong: a test that asserts something the spec does not say, or contradicts it. Quote the spec line, then the test.
        Vacuous: a test that would pass whether or not the feature works, or one that passed when you ran it even though the feature does not exist yet. Say why it passes.
        Ambiguous: places where the spec is too vague to tell whether the test is right. Ask me about these directly, most important first, 5 or fewer.

    Ignore test naming, formatting, file layout, and anything else about style.

```

### Discuss and post a comment

Continue to discuss the tests with Agent 2 until you are comfortable that you understand them. Compare them to the original specification. Do not just accept what Agent 2 says. Do your best to understand the tests, what they are doing, and whether you agree with Agent 2's concerns. Write in your answers to any questions remaining from Agent 2 about ambiguous tests. Then ask Agent 2 to post a new comment on the PR:

```
Please post this review and my responses as a new comment on the PR.
```

### Give test review back to Agent 1


```
Please see the recent comment on the PR. It contains findings from test review, and my answers to the ambiguous ones. Please fix every problem found with the tests. Apply my answers to the spec, folding each into the section it belongs to and adding them to the question log. Run the test suite again and report back: every test should be present, every test should be running, every test should be failing. If you disagree with any of the findings, please justify why. If there are any tests that are challenging to write or require decisions, consider the alternatives, discuss their pros and cons, and present your recommendation.

When you are done, commit the revised tests and a log of what you changed. 
```

Repeat this process until you and Agent 2 are satisfied with the tests. Consider also consulting a third agent running on a different AI model. 

## 4. Build

### 
Agent 1 writes code until every test passes. Here is an example prompt:

```
Read specs/NN-yourfeaturename.md in full, including the question log at the bottom, and every file in tests/. Implement the feature so that every test passes.

Rules:
- You may not touch the tests. No edits, no deletes, no skips, no weakening an assertion. If you believe a test is wrong, say so in a comment on the pull request and wait for me.
- Build only what the spec says. The "does not do" section binds you too.
- Commit in small steps with clear messages.
```

### Code review

Ask Agent 2 and optionally other AIs to do a code review on the finished work.

```
Review the code on pull request #__. Read the spec first, including the question log, then the diff. Do not edit any code.

Check: does the code do everything the spec says, and refuse everything in the "does not do" section? Any bugs, edge cases, or hostile inputs handled wrong? Any test that looks weakened, skipped, or edited to fit the code?

Remember not to be overeager to find issues. Stick to real, important, verified issues. 

Ignore naming, formatting, and file layout. End with a verdict: "approve", or a ranked list of what must change. Order the findings by severity.
````

### Discuss and post comment

Discuss the code review with Agent 2.

```
Post your findings and my responses as a review comment on the PR itself so there is a record. In each comment say what is wrong, the severity, why it matters, and what to do instead. 
```

### Builder revises
The code review is posted as comments on the PR. Give the PR to Agent 1 with a prompt like this:

```
Here is the code review, posted as comments on the pull request. Read every comment and reply under each one, either "Fixed. Here's the test that proves it." or "I disagree, because ___." Then fix every comment you accept and push the fixes as new commits to the same PR. You still may not touch the tests. If fixing a comment would require changing a test, do not change it: reply and wait for me.

When you are done, post one summary comment on the PR listing which comments you fixed and which you disputed, with your reasons. I will decide the disagreements.
```

When builder and reviewer disagree, **you decide.** You own what the app should
do. Neither of them does.

Repeat until there are no major findings in the code review.

## 5. User tests

Open the app yourself, on a real device, and try to use the feature the way the person in your user story would. Be sure to stress test it the way you actually use it, on your actual device, on the network you actually have.

When done, ask an agent log your findings:

```
Please log these findings at the bottom of the spec log: 
...

Then commit.
```

And record what you tried, what you expected, what happened, and which step you sent it back to. 

Bug? --> Back to Step 3
Spec was wrong? --> Back to Step 2
Design was wrong? --> Back to Step 1

All good? Proceed to step 6. 

## 6. Merge the code

Click "Merge" in the PR on github. Then: ask an agent to update `docs/backlog.md` status, add a line to `CHANGELOG.md`, and start the next item in your backlog!

## Note: the test suite also runs on GitHub

`.github/workflows/tests.yml` runs your tests on a clean machine every time a
pull request is opened or pushed to. You never have to start it.

It stays quiet while a pull request is a **draft**, which is where the red phase
belongs. Mark it ready for review once the tests pass, and that's when GitHub
runs them.

Its job is to catch the one thing you can't catch yourself: your project working
on your laptop only because you installed something in September and forgot to
write it down. That's the most common reason a classmate can't run your project
in Stage 3.

**If it goes red,** read the log. Either a test genuinely failed, or a dependency
is missing from `requirements.txt`. Both are worth fixing now rather than in
week 11. It is free on public repositories.

---

