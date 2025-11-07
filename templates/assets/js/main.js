// Minimal Webix app with login + product list demo
webix.ui({
  container: "app",
  rows:[
    { view:"template", template:"<h2>Smart Retail POS Insight</h2>", height:50 },
    {
      cols:[
        { gravity:2,
          rows:[
            { view:"form", id:"loginForm", elements:[
                { view:"text", name:"username", label:"Username"},
                { view:"text", type:"password", name:"password", label:"Password"},
                { view:"button", value:"Login", click: function(){
                    const v = $$("loginForm").getValues();
                    webix.ajax().post("/api/auth/login", v, function(text, xml, xhr){
                      const res = JSON.parse(text);
                      if(res.token) {
                        localStorage.setItem("token", res.token);
                        webix.message("Login success");
                        $$("productTable").reload();
                      } else {
                        webix.message("Login failed");
                      }
                    });
                }}
            ], width:300}
          ]
        },
        { gravity:5,
          rows:[
            { view:"toolbar", cols:[ { view:"label", label:"Products" }, { view:"button", value:"Refresh", width:90, click:() => $$("productTable").reload() } ] },
            { view:"datatable", id:"productTable", autoConfig:true, url:{
                load:function(params, callback){
                  const token = localStorage.getItem("token") || "";
                  webix.ajax().headers({"Authorization":"Bearer "+token}).get("/api/products", callback);
                }
            }, height:400}
          ]
        }
      ]
    }
  ]
});
