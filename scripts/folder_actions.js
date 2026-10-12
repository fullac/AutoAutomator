// System Events scripting dictionary; request is data, never executable source.
function run(argv) {
    const request = JSON.parse(argv[0]);
    const events = Application('System Events');
    function snapshot() {
        return {
            enabled: events.folderActionsEnabled(),
            actions: events.folderActions().map(function(action) {
                return {path: action.path(), enabled: action.enabled(),
                    scripts: action.scripts().map(function(script) {
                        return {path: script.posixPath(), enabled: script.enabled()};
                    }).sort(function(a, b) { return a.path.localeCompare(b.path); })};
            }).sort(function(a, b) { return a.path.localeCompare(b.path); })
        };
    }
    function findAction() {
        return events.folderActions().filter(function(a) { return a.path() === request.folder; })[0];
    }
    if (request.operation === 'snapshot') return JSON.stringify(snapshot());
    if (request.operation === 'enabled') {
        events.folderActionsEnabled = request.enabled;
    } else if (request.operation === 'bind') {
        let action = findAction();
        if (!action) {
            action = events.FolderAction({name: request.folder.split('/').pop(), path: request.folder});
            events.folderActions.push(action);
            action = findAction();
        }
        if (action.scripts().some(function(s) { return s.posixPath() === request.script; }))
            throw new Error('script already bound');
        const scriptPath = events.files.byName(request.script).path();
        action.scripts.push(events.Script({name: request.script.split('/').pop(), path: scriptPath}));
        action.enabled = true;
        events.folderActionsEnabled = true;
    } else if (request.operation === 'unbind') {
        const action = findAction();
        if (action) {
            action.scripts().filter(function(s) { return s.posixPath() === request.script; }).forEach(function(s) { events.delete(s); });
            if (request.created && action.scripts().length === 0) events.delete(action);
            else if (!request.created) action.enabled = request.previousEnabled;
        }
    } else {
        throw new Error('unknown operation');
    }
    return JSON.stringify(snapshot());
}
