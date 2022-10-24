// ==UserScript==
// @name         sounds.bl.uk-auto
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Try to archive something totally tricky.
// @author       Andrew Jackson <Andrew.Jackson@bl.uk>
// @match        https://sounds.bl.uk/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=bl.uk
// @grant        none
// ==/UserScript==

(async function() {
    'use strict';

    // e.g. https://sounds.bl.uk/Arts-literature-and-performance/Theatre-Archive-Project/

    async function sleep(ms){
        return new Promise(function (resolve, reject) {
            setTimeout(()=>{
                resolve();
            },ms);
        })
    }

    async function open_all_lists() {
        while(true) {
            var l = document.querySelectorAll('div[aria-hidden="false"] li[class="closed"] a');
            console.log(l);
            if ( l.length > 0 ) {
                for ( var e of l ) {
                    e.click();
                    // Nice big gap to try and make sure the audio gets to start playing...
                    await sleep(10*1000);
                }
            } else {
                break;
            }
        }
    }

    // Note that this doens't really work in Chrome because https://developer.chrome.com/blog/autoplay/ so need to override that for automation to work fully
    async function run_all_players() {
        var ps = document.querySelectorAll(".playable");
        for (var button of ps) {
            button.click();
            await sleep(1000);
        }
    }


    await sleep(4000);

    // Run players:
    await run_all_players();

    // Open all lists on first tab:
    await open_all_lists();

    // Iterate over other tabs:
    var tabs = document.querySelectorAll(".tabbedContent > ul > li > a");
    for( var tab of tabs ) {
        // Switch tab:
        tab.click();
        await sleep(2000);
        // Iterate over closed list items:
        await open_all_lists();
    }

})();