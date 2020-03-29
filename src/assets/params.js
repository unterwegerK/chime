
// todo: should this autosave on edit or on a button
const save_params_to_hash = (params, reset=false) => {
    /*
    Converts an object of key/value pairs to a url hash

    params: object --> with key: value pairs
    reset: boolean --> whether or not to reset the url hash
    returns: str --> url hash that is created
     */
    if( reset ){
        window.location.hash = "";
    }
    for( let param in params ){
        let key = param;
        let value = params[param];
        window.location.hash += key + "=" + value + ";";
    }
    return window.location.hash;
};

const gather_params = () => {
    /*
    Loops through the form classes and gathers the ids and values.
    Likely to send to save_params_to_hash.
    No arguments, but classes could be moved to arguments
    returns: object --> key/value pairs of params to save
     */
    let classes = ["form-control", "custom-control-input"],
        params = {};
    for( let class_name of classes ){
        for( let input of document.getElementsByClassName(class_name) ){
            params[input.id] = input.value;
        }
    }
    return params;
};

const get_params_from_hash = () => {
    /*
    Converts the url hash to an object of key/value pairs.
    The key is the html input id.
    No arguments.
    Returns: object --> key/value pairs
     */

    let hash_params = window.location.hash.substring(1);  // Get rid of the #
    hash_params = hash_params.split(";");

    let new_params = {};
    for (let p of hash_params) {
        if (p === "") {
            continue;
        }
        let kv = p.split("="),
            key = kv[0],
            value = kv[1];
        new_params[key] = value;
    }
    return new_params;
};


const update_sidebar_params = (params) => {
    /*
    Updates the values in the sidebar based on an object of key/value pairs, likely from the hash.
    Warning: This does not actually update the charts at the moment. Triggering the change/blur/enter on
        these inputs is not updating the charts.

    params: object --> key/value pairs, likely from get_params_from_hash
    returns: null
     */

    for( let param in params ) {
        let key = param,
            value = params[param];

        // These are the on/off "checkboxes"
        if (key.startsWith("_")) {
            let current_value = document.getElementById(key).value;
            if (current_value !== value) {  // toggle on/off
                document.getElementById(key).click();
            }
        } else {  // These are the normal inputs
            document.getElementById(key).value = value;
        }
        // attempt to trigger a change - Note: not currently working
        document.getElementById(key).dispatchEvent(new Event("change"));
    }
    return null;
};


// Could probably replace this with a jquery-style .ready function
// Note: commented out for now to make this inactive.
// let c = 0;
// let dom_ready = setInterval(function(){
//     console.log(c++);
//     if( document.getElementById('n_days') != null) {  // assumes n_ready. todo: add that to tests
//         clearInterval(dom_ready);
//         on_load();
//     } else if( c > 200 ){
//         clearInterval(dom_ready);  // took over 2 seconds to load the dom... No go.
//     }
// }, 10);

const hash_to_sidebar = () => {
    /*
    Shortcut function to grab params from the hash and update the sidebar with them.
     */
    update_sidebar_params(get_params_from_hash());
    return null;
};

const save_to_hash = () => {
    /*
    Shortcut function to gather the params from the sidebar and save them to the hash,
    resetting the hash in the process.
     */
    save_params_to_hash(gather_params(), true);
};

const on_load = () => {
    /*
    This function is triggered by the currently commented out interval above.
    It will grab the hash, update the sidebar, and watch for changes to the hash and update the sidebar.
     */
    hash_to_sidebar();
    // window.onhashchange = hash_to_sidebar;
};
