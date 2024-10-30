# Contributing to ansible-storage-protect

Thank you for your interest in contributing to our open-source ansible-storage-protect project.

To ensure that the codebase is always healthy and does not result in deployment issues when forked and used, it is important 
that you pre-check your additions and updates for any potential code conflicts before uploading your changes to the GitHub Repository.

Therefore, the following steps should be followed to submit your contributions:

1. Fork the repository
1. Create and run Ansible Test Playbooks
1. Commit/Push changes to your fork
1. Create a Pull Request

### 1. Fork the repository

To fork the repository:

* Get started by clicking on "Fork" from the top-right corner of the main repository page.
* Choose a name and description for your fork.
* Select the option "Copy the main branch only", as in most cases, you will only need the default branch to be copied.
* Click on "Create fork".

Once you have forked the repository, you can then clone your fork to your computer locally. In order to do that:
* Click on "Code" (the green button on your forked repository).
* Copy the forked repository URL under HTTPS.
* Type the following on your terminal:
```
git clone <the_forked_repository_url> 
```
You can set up Git to pull updates from the `ansible-storage-protect` repository into the local clone of your fork when you fork a 
project in order to propose changes to the `ansible-storage-protect` repository. In order to do that, run the following command:
```
git remote add upstream https://github.com/IBM/ansible-storage-protect
```
To verify the new upstream repository you have specified for your fork, run the following command:
```
git remote -v
```
You should see the URL for your fork as origin, and the URL for the `ansible-storage-protect` repository as upstream.

Now, you can work locally and commit to your changes to your fork. This will not impact the main branch.

Refer to the [naming conventions](Conventions.md), while developing your modules, roles, tests and playbooks.

### 2. Create and run Ansible Test Playbooks

Before committing changes, ensure that they work with the main codebase.

In the repository, navigate to “~/tests/playbooks”. You will find a group of YAML playbooks that will ensure the 
deployment is still successful with your proposed changes.

For any additions you contribute with, you will also need to write “assert that” statements to confirm that your 
changes will not break the codebase or cause any issues. You can go through the Python files in the directory to 
get an idea of how these Test Playbooks should be structured.

After writing your Test Playbooks, make sure to include them in the “main.py” file to execute all of the 
Test Playbooks at once. It will look something like this:
```
subprocess.run(['ansible-playbook', '--inventory', 'inventory.ini', 'playbook_name.yml'])
```
If the playbook runs successfully and no errors are displayed, then proceed to Step #3.

### 3. Commit/Push changes to your fork

If you are looking to add all the files you have modified in a particular directory, you can stage them all 
with the following command:
```
git add .
```
If you are looking to recursively add all changes including those in subdirectories, you can type:
```
git add -A
```
Alternatively, you can type `git add -all` for all new files to be staged.

Once you are ready to submit your changes, ensure that you commit them to your fork with a message. 
The commit message is an important aspect of your code contribution; it helps the maintainers of 
`ansible-storage-protect` and other contributors to fully understand the change you have made, 
why you made it, and how significant it is. You must use the [Commit Message Format](#commit-message-format).

You can commit your changes by running:
```
git commit -m "<type>(<scope>): <short summary of your changes/additions>"
```
To push all your changes to the forked repo:
```
git push
```
### 4. Create a Pull Request

Merge any changes that were made in the original repository’s main branch:
```
git merge upstream/main
```
Before creating a Pull Request, ensure you have read the [IBM Contributor License Agreement](CLA.md). 
By creating a PR, you certify that your contribution:
* is licensed under Apache Licence Version 2.0.
* does not result in IBM MQ proprietary code being statically or dynamically linked to Ansible runtime.

Once you have carefully read and agreed to the terms mentioned in the [CLA](CLA.md), you are ready to make 
a pull request to the original repository.

Navigate to your forked repository and press the New pull request button. Then, you should add a title and a 
comment to the appropriate fields and then press the Create pull request button.

The maintainers of the original repository will then review your contribution and decide whether or not to accept your pull request.

---

## Developer's Certificate of Origin and Signed-off-by

The sign-off is a simple line at the end of the explanation for the patch, which certifies that you wrote it or otherwise have the right to pass it on as an open-source patch.

With the Signed-off-by line you certify the below:

Developer's Certificate of Origin 1.1
```
       By making a contribution to this project, I certify that:

       (a) The contribution was created in whole or in part by me and I
           have the right to submit it under the open source license
           indicated in the file; or

       (b) The contribution is based upon previous work that, to the best
           of my knowledge, is covered under an appropriate open source
           license and I have the right under that license to submit that
           work with modifications, whether created in whole or in part
           by me, under the same open source license (unless I am
           permitted to submit under a different license), as indicated
           in the file; or

       (c) The contribution was provided directly to me by some other
           person who certified (a), (b) or (c) and I have not modified
           it.

       (d) I understand and agree that this project and the contribution
           are public and that a record of the contribution (including all
           personal information I submit with it, including my sign-off) is
           maintained indefinitely and may be redistributed consistent with
           this project or the open source license(s) involved.
```
If you can certify the above, just add a line stating the following at the bottom of each of your commit messages:

```
Signed-off-by: Developers Name <name@developer.com>
```
Use your real name and a valid e-mail address (no pseudonyms or anonymous contributions).

---

## Commit Message Format

This specification is inspired by the [AngularJS commit message format](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit).

We have very precise rules over how our Git commit messages must be formatted. This format leads to easier to read commit history.

Each commit message consists of a **header**, a **body**, and a **footer**.
```
<header>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```
The `header` is mandatory and must conform to the [Commit Message Header](#commit-message-header) format.

The body is mandatory for all commits except for those of type "docs". When the body is present it must be at least 20 characters long and must conform to the [Commit Message Body](#commit-message-body) format.

The footer is optional. The [Commit Message Footer](#commit-message-footer) format describes what the footer is used for and the structure it must have.

### Commit Message Header
```
<type>(<scope>): <short summary>
  │       │             │
  │       │             └─⫸ Summary in present tense. Not capitalized. No period at the end.
  │       │
  │       └─⫸ Commit Scope: modules|module_utils|roles|playbooks|inventories|tests|
  │
  └─⫸ Commit Type: feature|fix|refactor|test|docs|build|
```
The `<type>` and `<summary>` fields are mandatory, the (`<scope>`) field is optional.

#### Type

Must be one of the following:

* **feature**: A new feature
* **fix**: A bug fix
* **refactor**: A code change that neither fixes a bug nor adds a feature
* **test**: Adding missing tests or correcting existing tests
* **docs**: Documentation only changes
* **build**: Changes that affect the build system or external dependencies

#### Scope

The scope should be the name of the npm package affected (as perceived by the person reading the changelog generated from commit messages).

The following is the list of supported scopes:
* **modules**
* **module_utils**
* **roles**
* **playbooks**
* **inventories**
* **tests**

#### Summary

Use the `<short summary>` field to provide a succinct description of the change:
* use the imperative, present tense: "change" not "changed" nor "changes"
* don't capitalize the first letter
* no dot (.) at the end

### Commit Message Body

Just as in the summary, use the imperative, present tense: "fix" not "fixed" nor "fixes".

Explain the motivation for the change in the commit message body. This commit message should explain why you are making the change. You can include a comparison of the previous behavior with the new behavior in order to illustrate the impact of the change.

### Commit Message Footer

The footer can contain information about breaking changes and deprecations and is also the place to reference GitHub issues, Jira tickets, and other PRs that this commit closes or is related to. For example:

```
BREAKING CHANGE: <breaking change summary>
<BLANK LINE>
<breaking change description + migration instructions>
<BLANK LINE>
<BLANK LINE>
Fixes #<issue number>
```
or
```
DEPRECATED: <what is deprecated>
<BLANK LINE>
<deprecation description + recommended update path>
<BLANK LINE>
<BLANK LINE>
Closes #<pr number>
```
Breaking Change section should start with the phrase `BREAKING CHANGE`:  followed by a summary of the breaking change, a blank line, and a detailed description of the breaking change that also includes migration instructions.

Similarly, a Deprecation section should start with `DEPRECATED`:  followed by a short description of what is deprecated, a blank line, and a detailed description of the deprecation that also mentions the recommended update path.

### Revert commits

If the commit reverts a previous commit, it should begin with `revert: `, followed by the header of the reverted commit.

The content of the commit message body should contain:
* information about the SHA of the commit being reverted in the following format: This reverts commit <SHA>,
* a clear description of the reason for reverting the commit message.

---

## License

All contributions have to be submitted under the APL 2.0 license. See also the [LICENSE](./LICENSE) file.

---
