const urlParams = new URLSearchParams(window.location.search);
console.log(urlParams);
console.log(urlParams.has('test'));
console.log(urlParams.get('a'));