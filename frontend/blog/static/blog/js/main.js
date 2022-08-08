'use strict';

// https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
const getCookie = name => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; ++i) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

const postData = async (url, data) => {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(data),
    });
    return await response.json();
};

const voteListener = event => {
    event.preventDefault();

    const {type, id, action} = event.target.dataset;

    postData(`/blog/${type}/${id}/${action}`,{'obj': id})
        .then(json => {
            document.querySelector(`[data-id="${id}"][data-count="rating"]`).innerHTML = json.rating;
        });
};

['upvote', 'downvote'].forEach(action => {
   document.querySelectorAll(`[data-action="${action}"]`)
       .forEach(element => element.addEventListener('click', voteListener));
});
