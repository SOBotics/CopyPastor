// code taken from the example mentioned here https://github.com/kpdecker/jsdiff

function disp(one, other) {

  one = one.replace("<//script>", "</script>").replace("$//{", "${")
  other = other.replace("<//script>", "</script>").replace("$//{", "${")

  var color = '',
      span = null;

  var diff = JsDiff.diffWords(one, other),
      display = document.getElementById('display'),
      fragment = document.createDocumentFragment();

  diff.forEach(function(part) {
    // green for additions, red for deletions
    // grey for common parts
    color = part.added ? 'black' :
        part.removed ? 'green' : 'red';
    span = document.createElement('span');
    span.style.color = color;
    span.appendChild(document.createTextNode(part.value));
    fragment.appendChild(span);
  });

  display.appendChild(fragment);
}

function disp_sbs(one, other) {

  one = one.replace("<//script>", "</script>").replace("$/{", "${")
  other = other.replace("<//script>", "</script>").replace("$/{", "${")

  var color = '',
      span = null;

  var diff = JsDiff.diffWords(one, other),
    left = document.getElementById('left'),
    right = document.getElementById('right'),
    left_fragment = document.createDocumentFragment(),
    right_fragment = document.createDocumentFragment();

  diff.forEach(function(part) {
    // green for additions, red for deletions
    // grey for common parts
    color = part.added ? 'black' :
      part.removed ? 'green' : 'red';
    span = document.createElement('span');
    span.style.color = color;
    span.appendChild(document.createTextNode(part.value));

    switch (color) {

      case 'red':
        span_clone = span.cloneNode(true)
        left_fragment.appendChild(span);
        right_fragment.appendChild(span_clone);
        break;

      case 'black':
        right_fragment.appendChild(span);
        break;

      case 'green':
        left_fragment.appendChild(span);
        break;
    }

  });

  left.appendChild(left_fragment);
  right.appendChild(right_fragment);
}