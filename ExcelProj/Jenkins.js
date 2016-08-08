// ==UserScript==
// @name         jenkins
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  try to take over the world!
// @author       Aaron Iniguez
// @match        http://jenkins-smt.cal.ci.spirentcom.com:8080/
// @match        http://jenkins-smt.cal.ci.spirentcom.com:8080/job/*
// @require     https://ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js
// @grant   GM_getValue
// @grant   GM_setValue
// ==/UserScript==

//to use: run the script on the jenkins page and wait for the last page to popup, save the contents of the console output into a csv file and then open in excel
(function() {
    var myvar = "";
    var domain = "http://jenkins-smt.cal.ci.spirentcom.com:8080";
    var agentIdent = "CI_AGENT_LIST";
    var smIdent = "SM_IP";
    if (window.location.href.indexOf("job") == -1){
        //first order the columns by time 
        //$("th:nth-child(4) .sortheader").click();
        //from the job column in jenkins get jobname and joburl
        GM_setValue("contents", "");
        var jobList = [];
        $(".healthReport+ td .inside").each(
            function()
            {
                jobList.push({"jobname":$(this).text(), "agents":[], "suitemaster":"", "jobUrl":domain+"/"+$(this).attr("href"), "date":""});
            }
        );
        var date = [];
        //from the date column get the date
        $("td:nth-child(4)").each(
            function(index)
            {
                if ($(this).text().length !== 0){
                    date.push($(this).text());
                }
            }
        );
        for (var i = 0; i < jobList.length;i++){
            jobList[i].date = date[i];
        }
        //remove the jobs that have a date 2 months and older
        for (var i = 0; i < jobList.length; i++){
            if (jobList[i].date.indexOf("yr")!= -1 || jobList[i].date.indexOf("N/A")!=-1 || jobList[i].date.indexOf("2 mo")!=-1 || jobList[i].date.indexOf("3 mo")!=-1|| jobList[i].date.indexOf("4 mo")!=-1|| jobList[i].date.indexOf("5 mo")!=-1
                || jobList[i].date.indexOf("6 mo")!=-1|| jobList[i].date.indexOf("7 mo")!=-1|| jobList[i].date.indexOf("8 mo")!=-1|| jobList[i].date.indexOf("9 mo")!=-1|| jobList[i].date.indexOf("10 mo")!=-1|| jobList[i].date.indexOf("11 mo")!=-1
                || jobList[i].date.indexOf("12 mo")!=-1){
                delete jobList[i];
            }
        }
        GM_setValue("stopat", jobList[Object.keys(jobList).length-1].jobname);
        //remove the jobs that have the words -Results, -Upgrade, -Restart, and -Maintenance
        for (var i =0; i< jobList.length; i++){
            if (typeof jobList[i] != "undefined"){
                if (jobList[i].jobname.indexOf("-Results")!=-1 || jobList[i].jobname.indexOf("-Upgrade")!=-1 || jobList[i].jobname.indexOf("-Restart")!=-1|| jobList[i].jobname.indexOf("-Maintenance")!=-1){
                    delete jobList[i];
                }
            }
        }
        //save last job name so we know where to stop
        //open a new job every 1.5 seconds
        function doSetTimeout(i) {
            setTimeout(function() { window.open(jobList[i].jobUrl); }, i*2000);
        }
        for (var i = 1; i <= jobList.length; ++i)
            doSetTimeout(i);
    }
    else if (window.location.href.indexOf("parameters") == -1 && window.location.href.indexOf("ws")==-1){
        window.location.href = domain+$(".zws-inserted").first().attr("href")+"parameters";
    }
    else if(window.location.href.indexOf("parameters")!=-1 && window.location.href.indexOf("ws")==-1){
        var contents = GM_getValue("contents");
        var jobName = window.location.href.split("job/")[1].split("/")[0];
        contents = contents + "\n"+jobName;
        $(".setting-name").each(function(index){
            //for each .setting-name check if name property is equal to SM_IP(suite master name) then get value
            if ($(this).text() == smIdent){
                contents = contents + ","+$(".setting-input").eq(index).val()+",";
            }
            //for each .setting-name check if name property is equal to agentIdent(agent host name) then get value
            if ($(this).text() == agentIdent){
                var hostname = $(".setting-input").eq(index).val().split("hostname':'");
                for (var i =1; i < hostname.length; i++){
                    //add a " before you start writing agent names so newlines work in a cell
                    if (contents[contents.length-1] == ","){
                        contents = contents+"\""+hostname[i].split("','platform")[0];
                    }
                    else{
                        contents = contents +"\n"+hostname[i].split("','platform")[0];
                    }
                    //end the agent cell with a " 
                    if (i == hostname.length -1){
                        contents = contents+"\"";
                    }
                }
            }
        });
        GM_setValue("contents", contents);
        var newUrl = domain+"/job/"+jobName+"/ws/";
        window.location.href = newUrl;
    }
    else if(window.location.href.indexOf("ws")!=-1){
        //parse the text file and look for agent hostnames and then add it to variable contents
        if (window.location.href.indexOf("tx")!=-1){
            var allhosts = [];
            var hosts = document.documentElement.innerHTML.split("'hostname':'");
            hosts.shift();
            console.log(hosts);
            for (var i =0; i < hosts.length; i++){
                allhosts.push(hosts[i].split("'")[0]);
            }
            //case: name,sm,"agent hostnames"
            var contents = GM_getValue("contents");
            if (contents[contents.length-1]=="\""){
                contents = contents.slice(0, -1);
            }
            //case: name
            else if (contents[contents.length-1]!=","){
                contents = contents+",,\"";
            }
            //case: name, sm,
            else{
                contents = contents +"\"";
            }
            GM_setValue("contents", contents+allhosts.join("\n")+"\"");
            if (window.location.href.indexOf(GM_getValue("stopat"))!=-1){
                window.close();
            }
        }
        $("td:nth-child(2) a").each(function(){
            if ($(this).text().indexOf("Resource")!=-1 && $(this).text().indexOf(".txt")!=-1){
                window.open(window.location.href + $(this).attr("href"));
            }
        });
        if (window.location.href.indexOf(GM_getValue("stopat"))==-1){
            window.close();
        }
        else{
            console.log(GM_getValue("contents"));
        }
    }

})();