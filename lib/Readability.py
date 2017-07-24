import re
import urllib2
from bs4 import BeautifulSoup



ATTR_CONTENT_SCORE = "contentScore"
DOM_DEFAULT_CHARSET = "utf-8"
MESSAGE_CAN_NOT_GET = "Readability was unable to parse this page for content."

parent_nodes = []
junk_tags = ("style", "form", "iframe", "script", "button", "input", "textarea",
                 "noscript", "select", "option", "object", "applet", "basefont",
                 "bgsound", "blink", "canvas", "command", "menu", "nav", "datalist",
                 "embed", "frame", "frameset", "keygen", "label", "marquee", "link")
junk_attrs = ("style", "class", "onclick", "onmouseover", "align", "border", "margin")


def main(url):
    page = urllib2.urlopen(url).read()
    return get_content(BeautifulSoup(page, 'html.parser'))


def remove_junk_tags(node):
    for tag in junk_tags:
        [s.extract() for s in node(tag)]
    return node


def remove_junk_attrs(node):
    for attr in junk_attrs:
        node[attr] = None
    return node


def get_top_box(soup):
    all_paragraphs = soup.find_all("p")
    for paragraph in all_paragraphs:
        parentNode   = paragraph.parent
        contentScore = 0 if ATTR_CONTENT_SCORE not in parentNode else parentNode[ATTR_CONTENT_SCORE]
        className = parentNode.get('class')
        if className and len(className) >= 1:
            className = className[0]
        id = parentNode.get('id')
        if className and re.match("(comment|meta|footer|footnote)", className) is not None:
            contentScore -= 50
        elif className and re.match(
            "((^|\\s)(post|hentry|entry[-]?(content|text|body)?|article[-]?(content|text|body)?)(\\s|$))",
            className
        ) is not None:
            contentScore += 25

        if id and re.match("/(comment|meta|footer|footnote)/i", id) is not None:
            contentScore -= 50
        elif id and re.match(
            "^(post|hentry|entry[-]?(content|text|body)?|article[-]?(content|text|body)?)$",
            id
        ) is not None:
            contentScore += 25

        if len(str(paragraph)) > 10:
            contentScore += len(str(paragraph))

        parentNode[ATTR_CONTENT_SCORE] = contentScore
        parent_nodes.append(parentNode)

    top_box = None

    for key, node in enumerate(parent_nodes):
        contentScore    = int(node[ATTR_CONTENT_SCORE])
        orgContentScore = 0 if top_box is None else int(top_box[ATTR_CONTENT_SCORE])
        if contentScore > orgContentScore:
            top_box = node
    return top_box


def get_title(node):
    split_point = ' - '
    titleNodes = node.find_all("title")
    if len(titleNodes) > 0:
        titleNode = titleNodes[0]
        title = titleNode.string
        result = title.split(split_point, 1)
        return result[-1].strip() if len(result) > 1 else title.strip()
    return None


def get_lead_image_url(node):
    images = node.find_all("img")
    if len(images) > 0:
        leadImage = images[0]
        return leadImage.get('src')
    return None


def get_content(soup):
    if not soup:
        return False

    content_title = get_title(soup)
    content_box = get_top_box(soup)

    if content_box is None:
        raise Exception('Unable to get content')

    content_box = remove_junk_tags(content_box)
    content_box = remove_junk_attrs(content_box)

    return {
        'lead_image_url': get_lead_image_url(content_box),
        'word_count': len(content_box),
        'title': content_title,
        'content': content_box,
    }

def my_handler(event, context):
    url = 'http://mashable.com/2017/07/23/teen-groot-infinity-war-movies-comic-con-footage-guardians-marvel/?utm_cid=hp-hh-pri#Z8uhiFmk2qqQ'
    print main(url)
