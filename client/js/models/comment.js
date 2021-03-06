'use strict';

const api = require('../api.js');
const events = require('../events.js');

class Comment extends events.EventTarget {
    constructor() {
        super();
        this._updateFromResponse({});
    }

    static create(postId) {
        const comment = new Comment();
        comment._postId = postId;
        return comment;
    }

    static fromResponse(response) {
        const comment = new Comment();
        comment._updateFromResponse(response);
        return comment;
    }

    get id()           { return this._id; }
    get postId()       { return this._postId; }
    get text()         { return this._text; }
    get user()         { return this._user; }
    get creationTime() { return this._creationTime; }
    get lastEditTime() { return this._lastEditTime; }
    get score()        { return this._score; }
    get ownScore()     { return this._ownScore; }

    set text(value)    { this._text = value; }

    save() {
        const detail = {
            version: this._version,
            text: this._text,
        };
        let promise = this._id ?
            api.put('/comment/' + this._id, detail) :
            api.post(
                '/comments', Object.assign({postId: this._postId}, detail));

        return promise.then(response => {
            this._updateFromResponse(response);
            this.dispatchEvent(new CustomEvent('change', {
                detail: {
                    comment: this,
                },
            }));
            return Promise.resolve();
        }, response => {
            return Promise.reject(response.description);
        });
    }

    delete() {
        return api.delete(
                '/comment/' + this._id,
                {version: this._version})
            .then(response => {
                this.dispatchEvent(new CustomEvent('delete', {
                    detail: {
                        comment: this,
                    },
                }));
                return Promise.resolve();
            }, response => {
                return Promise.reject(response.description);
            });
    }

    setScore(score) {
        return api.put('/comment/' + this._id + '/score', {score: score})
            .then(response => {
                this._updateFromResponse(response);
                this.dispatchEvent(new CustomEvent('changeScore', {
                    detail: {
                        comment: this,
                    },
                }));
                return Promise.resolve();
            }, response => {
                return Promise.reject(response.description);
            });
    }

    _updateFromResponse(response) {
        this._version      = response.version;
        this._id           = response.id;
        this._postId       = response.postId;
        this._text         = response.text;
        this._user         = response.user;
        this._creationTime = response.creationTime;
        this._lastEditTime = response.lastEditTime;
        this._score        = parseInt(response.score);
        this._ownScore     = parseInt(response.ownScore);
    }
}

module.exports = Comment;
