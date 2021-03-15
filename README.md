# tsoha-forum
A forum, written for tsoha.

## Features

- [ ] Users can register, login, and logout.
- [ ] The front page has of a list of boards, showing the amount of
      topics and messages in each, as well as the date of the latest
      message in said board.
- [ ] Users can create new topics.
- [ ] Users can post new messages in existing topics.
- [ ] Users can modify their own topics and messages.
- [ ] Users can search for messages containing a word.
- [ ] Administrators can add and remove boards.
- [ ] Administrators can create secret boards, and specify which users
      have access to it.

## Running

Requirements: Python 3 and pip.

Run the following commands to get the server running on your machine:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run
```

Note: when deploying for production usage, there should be a reverse
proxy that accepts HTTPS connections in front of this server, to avoid
leaking sensitive information.

## License
This server software is distributed under the terms of the [GNU
AGPLv3](LICENSE) license.
