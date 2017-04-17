# Git Punch Card

### Setup

```bash
virtualenv env
. env/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
./punchcard.py /path/to/my/repo/.git
```

Optionally pass `--normalize` to normalize commits on a per-user basis.

### Example Output

![](https://raw.githubusercontent.com/x/Shitty-Git-Punch-Card/master/example_out.png)
