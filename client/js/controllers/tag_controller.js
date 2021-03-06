'use strict';

const router = require('../router.js');
const api = require('../api.js');
const misc = require('../util/misc.js');
const tags = require('../tags.js');
const Tag = require('../models/tag.js');
const topNavigation = require('../models/top_navigation.js');
const TagView = require('../views/tag_view.js');
const EmptyView = require('../views/empty_view.js');

class TagController {
    constructor(ctx, section) {
        if (!api.hasPrivilege('tags:view')) {
            this._view = new EmptyView();
            this._view.showError('You don\'t have privileges to view tags.');
            return;
        }

        Tag.get(ctx.parameters.name).then(tag => {
            topNavigation.activate('tags');
            topNavigation.setTitle('Tag #' + tag.names[0]);

            this._name = ctx.parameters.name;
            tag.addEventListener('change', e => this._evtSaved(e, section));

            const categories = {};
            for (let category of tags.getAllCategories()) {
                categories[category.name] = category.name;
            }

            this._view = new TagView({
                tag: tag,
                section: section,
                canEditAnything: api.hasPrivilege('tags:edit'),
                canEditNames: api.hasPrivilege('tags:edit:names'),
                canEditCategory: api.hasPrivilege('tags:edit:category'),
                canEditImplications: api.hasPrivilege('tags:edit:implications'),
                canEditSuggestions: api.hasPrivilege('tags:edit:suggestions'),
                canEditDescription: api.hasPrivilege('tags:edit:description'),
                canMerge: api.hasPrivilege('tags:merge'),
                canDelete: api.hasPrivilege('tags:delete'),
                categories: categories,
            });

            this._view.addEventListener('change', e => this._evtChange(e));
            this._view.addEventListener('submit', e => this._evtUpdate(e));
            this._view.addEventListener('merge', e => this._evtMerge(e));
            this._view.addEventListener('delete', e => this._evtDelete(e));
        }, errorMessage => {
            this._view = new EmptyView();
            this._view.showError(errorMessage);
        });
    }

    _evtChange(e) {
        misc.enableExitConfirmation();
    }

    _evtSaved(e, section) {
        misc.disableExitConfirmation();
        if (this._name !== e.detail.tag.names[0]) {
            router.replace(
                '/tag/' + e.detail.tag.names[0] + '/' + section, null, false);
        }
    }

    _evtUpdate(e) {
        this._view.clearMessages();
        this._view.disableForm();
        if (e.detail.names !== undefined) {
            e.detail.tag.names = e.detail.names;
        }
        if (e.detail.category !== undefined) {
            e.detail.tag.category = e.detail.category;
        }
        if (e.detail.implications !== undefined) {
            e.detail.tag.implications = e.detail.implications;
        }
        if (e.detail.suggestions !== undefined) {
            e.detail.tag.suggestions = e.detail.suggestions;
        }
        if (e.detail.description !== undefined) {
            e.detail.tag.description = e.detail.description;
        }
        e.detail.tag.save().then(() => {
            this._view.showSuccess('Tag saved.');
            this._view.enableForm();
        }, errorMessage => {
            this._view.showError(errorMessage);
            this._view.enableForm();
        });
    }

    _evtMerge(e) {
        this._view.clearMessages();
        this._view.disableForm();
        e.detail.tag.merge(e.detail.targetTagName).then(() => {
            this._view.showSuccess('Tag merged.');
            this._view.enableForm();
            router.replace(
                '/tag/' + e.detail.targetTagName + '/merge', null, false);
        }, errorMessage => {
            this._view.showError(errorMessage);
            this._view.enableForm();
        });
    }

    _evtDelete(e) {
        this._view.clearMessages();
        this._view.disableForm();
        e.detail.tag.delete()
            .then(() => {
                const ctx = router.show('/tags/');
                ctx.controller.showSuccess('Tag deleted.');
            }, errorMessage => {
                this._view.showError(errorMessage);
                this._view.enableForm();
            });
    }
}

module.exports = router => {
    router.enter('/tag/:name(.+?)/edit', (ctx, next) => {
        ctx.controller = new TagController(ctx, 'edit');
    });
    router.enter('/tag/:name(.+?)/merge', (ctx, next) => {
        ctx.controller = new TagController(ctx, 'merge');
    });
    router.enter('/tag/:name(.+?)/delete', (ctx, next) => {
        ctx.controller = new TagController(ctx, 'delete');
    });
    router.enter('/tag/:name(.+)', (ctx, next) => {
        ctx.controller = new TagController(ctx, 'summary');
    });
};
