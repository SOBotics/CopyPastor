
![CatPics](https://raw.githubusercontent.com/SOBotics/CopyPastor/master/static/favicon.png)

# CopyPastor

CopyPastor is a very small [Flask App](https://en.wikipedia.org/wiki/Flask_(web_framework)) to serve as a web dashboard for the [Guttenberg](https://stackapps.com/questions/7197/guttenberg-a-bot-searching-for-plagiarism-on-stack-overflow) bot project, whose purpose is to detect plagiarism on Stack Overflow and help raise plagiarism flags.

The final plan for this project is to demarcate the portions that may have been plagiarized clearly, and to compare them with the post that it may have been taken from.

CopyPastor records the score of the reported posts, and the reasons that it was caught by.

> Score: 0.7580878138542175; Reported for: String similarity

It also records the full text of both the post suspected to be plagiarized and the post that it was potentionally taken from, and the dates and authors of both.


# Setup

To setup the app on your local machine:

    git clone https://github.com/SOBotics/CopyPastor.git
    cd CopyPastor
    sh setup.sh
    flask run        # or python3 -m flask run
    
To learn about the API, you can check the [API Documentation](https://github.com/SOBotics/CopyPastor/wiki/API-Documentation) in the wiki.
