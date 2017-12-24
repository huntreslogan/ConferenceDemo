$(function () {
  console.log('Requesting Capability Token...');
  $.get('/capabilitytoken')
    .done(function (data) {
      console.log('Got a token.');
      console.log('Token: ' + data.token);

      // Setup Twilio.Device
      Twilio.Device.setup(data.token);

      Twilio.Device.ready(function (device) {
        device.sounds.outgoing(false);
        device.sounds.disconnect(false);
        console.log('Twilio.Device Ready!');

      });

      Twilio.Device.error(function (error) {
        console.log('Twilio.Device Error: ' + error.message);
      });

      Twilio.Device.connect(function (conn) {
        console.log('Successfully established call!');
      });

      Twilio.Device.disconnect(function (conn) {
        console.log('Call ended.');
      });
    })
    .fail(function (e) {
      console.error(e);
      console.log('Could not get a token from server!');
    });

    $('#leave-button').click(function() {
      console.log("hitting leave");
      Twilio.Device.disconnectAll();
      $('#leave-button').addClass('hide');
      $('#monitor-button').removeClass('hide');

    });

    $('#barge-button').click(function() {
      $("#barge-button").attr('disabled', true);
      $.post('/barge', function(data){
        console.log('barged in that thang');
      });
    });

    $('#monitor-button').click(function () {

      console.log('Calling ...');
      Twilio.Device.connect();
      $('#monitor-button').addClass('hide');
      $('#leave-button').removeClass('hide');
    });

    $('#whisper-button').click(function(){
      $.post('/update');
    });

    $.getJSON('/token', function (tokenResponse) {
      //Initialize the Sync client
      console.log(tokenResponse.token);
      syncClient = new Twilio.Sync.Client(tokenResponse.token, { logLevel: 'info' });
      syncClient.on('connectionStateChanged', function(state) {
        if (state != 'connected') {
          console.log('Sync is not live (websocket connection ' + state);
        } else {
          console.log('Sync is live and it is awesome!');
        }
      });

      //Let's pop a message on the screen to show that Sync is ready
      console.log('Sync initialized!');

      syncClient.document("AgentData").then(function(doc) {
          doc.on("updated",function(data) {
          console.log(data);

          if(data.call_status == 'conference-start'){
            $('#monitor-button').attr('disabled', false);
            $('#barge-button').attr('disabled', false);
            $('#whisper-button').attr('disabled', false);
            $("#customer").removeClass('hide');
            $("#no-customer").addClass('hide');
            $('#agent1-message').addClass('live');
            $('#agent1-message').removeClass('text-muted');
            $('#agent1-message').html('Live call');
          }

          if(data.call_status == 'conference-end'){
            $('#monitor-button').attr('disabled', true);
            $('#barge-button').attr('disabled', true);
            $('#whisper-button').attr('disabled', true);
            $("#customer").addClass('hide');
            $("#no-customer").removeClass('hide');
            $('#agent1-message').removeClass('live');
            $('#agent1-message').addClass('text-muted');
            $('#agent1-message').html('Waiting...');
          }

        });
      });

      });

    });
