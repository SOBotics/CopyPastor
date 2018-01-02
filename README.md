
![CatPics](https://raw.githubusercontent.com/SOBotics/CopyPastor/master/static/favicon.png)

# Copy Pastor

A very small Flask App to serve as a web dashboard for the [Guttenberg](https://stackapps.com/questions/7197/guttenberg-a-bot-searching-for-plagiarism-on-stack-overflow) bot which would help in the plagiarism flags.

The final plan is to demarcate the plagiarized portions clearly, and to compare it with the target post.

# API Call


## POST  `/posts/create`

POST Parameters:

    "url_one"   : The URL of the post which is (possibly) plagairized
    "url_two"   : The URL of the original post
    "title_one" : Title of the post which is (possibly) plagiarized
    "title_two" : Title of the original post
    "date_one"  : The date when the (possibly) plagiarized post was created
    "date_two"  : The date when the original post was created
    "body_one"  : The body markdown of the post which is (possibly) plagiarized
    "body_two"  : The body markdown of the original post

### Responses

Success Response

     {"post_id":<postID>,"status":"success"}

Failure Response

     {"message":<error reason>,"status":"failure"}


## GET `/posts/<post_id>`

A web view of the two posts next to each other.