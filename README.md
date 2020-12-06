# NixOS Security Tracker

This is (yet) another attempt at creating an overview of all the known
potentialy security issue within NixOS & Nixpkgs.

In contrast to my previous
[attempts](https://andreas.rammhold.de/posts/broken-sh/) this version tries to
primarily focus on the tracking of progress and issues. The software is develop to aid in current issue troubleshooting and features are added as needed. Some of the current goals include:

* Provide an index of all the commonly known CVEs where for each issue with all
  the references that upstream CVE sources already add to them.
* Each issue in the tracker allows setting a `status` to values such as
  `affected`, `notaffected`, `notforus` or `wontfix`. Those are meant to help
  later on when an issue bubbles up again or when another user idependently
  find it.
* Add references to Nixpkgs issues, commits and pull requests whenever a CVE is
  being mentioned there.
* Eventually creating advisories that contain one or more issues.


## Contributing

Please feel free to contribute to this project via either GitHub or send mails
to
[andi+nixos-security-tracker@notmuch.email](mailto:andi+nixos-security-tracker@notmuch.email).

This project is based on Django (a Python web framework) and all of the
features are covered by unit tests. Some of the feature are also (integration)
tested via NixOS VM tests. Please write tests for features and bugfixes that
you contribute to this repository.

For development all you need is Nix and `nix-shell`. The shell environment will
drop you into an environment where all the Python packages are available. There
is no need to manually run `poetry install` (or similar).

If you can not use `nix-shell` you should be able to get a working development
environment by installing all the python dependencies via `poetry`. Please also
read the section about `Code formatting` to properly format your code for
inclusion. This should avoid needless back and forth about code formatting.

Once you are in a suitable environment you can run unit- and e2e-tests via
`pytest` in the root of the repository.

### Commit messages

Comit messages should be the key documentation of a *why* a change has to be
made and what the benefits are. Commit messages such as `Updated something.py`
are not helping understanding the motivation behind a change. A few seconds now
will help save minutes down the road when someone reviews/git-blame's your
changes.

We do not (yet) enforce a specific style of commit messages but everyone is
encouraged to make them selfexplaining as much as possible.

That being said there are various "short" (or brief) commit message that are
acceptable as their goal is usually well known. A good example of this case is
updating our dependencies (either the python tooling or the Nix sources) where
a simple `Updated Nix dependencies` can abe acceptable. Even in those cases, if
you did not do the version bump for the sake of the version bump, please
include a motivation why you want to switch to a different version in the
commit message.


### Tests

For each new feature there should be an equivalent (new) test that verifies
that it is working. Please do not be shy about adding more than just the
minimal amount of tests for your feature. If at some point tests become too
slow we will handle that upstream.

The e2e tests are currently aiming at the high-level user interaction with the
application. Usually a journey or workflow through the website that uses many
of the individually tested features. If you contribute an entirely new workflow
consider adding one of those in addition to just the unit tests.

### Code formatting

This repository is using [editorconfig](https://editorconfig.org/) to define
some common rules around whitespaces throught the repository. Most of todays
editors support these settings either natively (vscode, …) or through a plugin
(vim, atom, sublime, …).

We are making use of `pre-commit` hooks to enforce formatting (amongst other
checks) on commit. When you use `nix-shell` (e.g. with `direnv`) for
development you'll have them set-up automatically.

Python formatting is handled by `black` and Nix code formatting is handled by
`nixpkgs-fmt`. While neither of these might produce code formatting you
personally like they provide consistency which is arguable more important in a
shared development setting.
