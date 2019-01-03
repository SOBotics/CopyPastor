function disp(one, other)
{
var color = '',
    span = null;

var diff = JsDiff.diffChars(one, other),
    display = document.getElementById('display'),
    fragment = document.createDocumentFragment();

diff.forEach(function(part){
  // green for additions, red for deletions
  // grey for common parts
  color = part.added ? 'black' :
    part.removed ? 'green' : 'red';
  span = document.createElement('span');
  span.style.color = color;
  span.appendChild(document
    .createTextNode(part.value));
  fragment.appendChild(span);
});

display.appendChild(fragment);
}