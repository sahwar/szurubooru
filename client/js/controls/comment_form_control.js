'use strict';

const events = require('../events.js');
const misc = require('../util/misc.js');
const views = require('../util/views.js');

const template = views.getTemplate('comment-form');

class CommentFormControl extends events.EventTarget {
    constructor(hostNode, comment, canCancel, minHeight) {
        super();
        this._hostNode = hostNode;
        this._comment = comment || {text: ''};
        this._canCancel = canCancel;
        this._minHeight = minHeight || 150;

        const sourceNode = template({
            comment: this._comment,
        });

        const previewTabButton = sourceNode.querySelector('.buttons .preview');
        const editTabButton = sourceNode.querySelector('.buttons .edit');
        const formNode = sourceNode.querySelector('form');
        const cancelButton = sourceNode.querySelector('.cancel');
        const textareaNode = sourceNode.querySelector('form textarea');

        previewTabButton.addEventListener(
            'click', e => this._evtPreviewClick(e));
        editTabButton.addEventListener(
            'click', e => this._evtEditClick(e));

        formNode.addEventListener('submit', e => this._evtSaveClick(e));

        if (this._canCancel) {
            cancelButton
                .addEventListener('click', e => this._evtCancelClick(e));
        } else {
            cancelButton.style.display = 'none';
        }

        for (let event of ['cut', 'paste', 'drop', 'keydown']) {
            textareaNode.addEventListener(event, e => {
                window.setTimeout(() => this._growTextArea(), 0);
            });
        }
        textareaNode.addEventListener('change', e => {
            this.dispatchEvent(new CustomEvent('change', {
                detail: {
                    target: this,
                },
            }));
            this._growTextArea();
        });

        views.replaceContent(this._hostNode, sourceNode);
    }

    enterEditMode() {
        this._freezeTabHeights();
        this._hostNode.classList.add('editing');
        this._selectTab('edit');
        this._growTextArea();
    }

    exitEditMode() {
        this._hostNode.classList.remove('editing');
        this._hostNode.querySelector('.tab-wrapper').style.minHeight = null;
        views.clearMessages(this._hostNode);
        this.setText(this._comment.text);
    }

    get _textareaNode() {
        return this._hostNode.querySelector('.edit.tab textarea');
    }

    get _contentNode() {
        return this._hostNode.querySelector('.preview.tab .comment-content');
    }

    setText(text) {
        this._textareaNode.value = text;
        this._contentNode.innerHTML = misc.formatMarkdown(text);
    }

    showError(message) {
        views.showError(this._hostNode, message);
    }

    _evtPreviewClick(e) {
        e.preventDefault();
        this._contentNode.innerHTML =
            misc.formatMarkdown(this._textareaNode.value);
        this._freezeTabHeights();
        this._selectTab('preview');
    }

    _evtEditClick(e) {
        e.preventDefault();
        this.enterEditMode();
    }

    _evtSaveClick(e) {
        e.preventDefault();
        this.dispatchEvent(new CustomEvent('submit', {
            detail: {
                target: this,
                comment: this._comment,
                text: this._textareaNode.value,
            },
        }));
    }

    _evtCancelClick(e) {
        e.preventDefault();
        this.exitEditMode();
    }

    _selectTab(tabName) {
        this._freezeTabHeights();
        const tabWrapperNode = this._hostNode.querySelector('.tab-wrapper');
        tabWrapperNode.setAttribute('data-tab', tabName);
        for (let tab of this._hostNode.querySelectorAll('.tab, .buttons li')) {
            tab.classList.toggle('active', tab.classList.contains(tabName));
        }
    }

    _freezeTabHeights() {
        const tabsNode = this._hostNode.querySelector('.tab-wrapper');
        const tabsHeight = tabsNode.getBoundingClientRect().height;
        tabsNode.style.minHeight = tabsHeight + 'px';
    }

    _growTextArea() {
        this._textareaNode.style.height =
            Math.max(
                this._minHeight || 0,
                this._textareaNode.scrollHeight) + 'px';
    }
};

module.exports = CommentFormControl;
