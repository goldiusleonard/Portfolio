package com.binus.myaddressbook;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.maps.CameraUpdateFactory;
import com.google.android.gms.maps.GoogleMap;
import com.google.android.gms.maps.OnMapReadyCallback;
import com.google.android.gms.maps.SupportMapFragment;
import com.google.android.gms.maps.model.LatLng;
import com.google.android.gms.maps.model.MarkerOptions;

import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class EmployeeDetailActivity extends AppCompatActivity {
    private ImageButton back_btn;
    private Button add_btn;

    private ImageView photo_profile;
    private TextView employee_name, employee_registered, employee_location, employee_phone, employee_email;

    private GoogleMap map;

    private String employeeID, first_name, last_name, city, country, phone, cell, email, image_path;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_employee_detail);

        photo_profile = findViewById(R.id.employee_photo);
        employee_name = findViewById(R.id.employee_name);
        employee_registered = findViewById(R.id.employee_registered);
        employee_location = findViewById(R.id.employee_location);
        employee_phone = findViewById(R.id.employee_phone);
        employee_email = findViewById(R.id.employee_email);
        add_btn = findViewById(R.id.add_btn);
        back_btn = findViewById(R.id.back_btn);

        back_btn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });

        add_btn.setEnabled(false);

        Intent intent = getIntent();
        employeeID = intent.getStringExtra("employee_id");

        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl("https://u73olh7vwg.execute-api.ap-northeast-2.amazonaws.com/")
                .addConverterFactory(GsonConverterFactory.create())
                .build();

        JSONPlaceholder jsonPlaceholder = retrofit.create(JSONPlaceholder.class);
        Call<resModel> call = jsonPlaceholder.getEmployee("stage2/people/" + employeeID + "/?nim=2301857102&nama=Goldius_Leonard");
        call.enqueue(new Callback<resModel>() {
            @Override
            public void onResponse(Call<resModel> call, Response<resModel> response) {
                if(!response.isSuccessful()) {
                    Toast.makeText(EmployeeDetailActivity.this, response.code(), Toast.LENGTH_SHORT).show();
                    return;
                }

                if (!response.body().getEmployees().isEmpty()) {
                    Employee employee = response.body().getEmployees().get(0);

                    Picture photo_paths = employee.getPicture();
                    image_path = photo_paths.getLarge();

                    Integer employeeId = employee.getEmployeeId();

                    Name names = employee.getName();
                    first_name = names.getFirst();
                    last_name = names.getLast();

                    Registered registered = employee.getRegistered();
                    String dateRegistered = registered.getDate();
                    String[] datePart = dateRegistered.split("-");

                    Calendar cal=Calendar.getInstance();
                    SimpleDateFormat month_date = new SimpleDateFormat("MMMM");
                    int monthnum = Integer.parseInt(datePart[1]);
                    cal.set(Calendar.MONTH, monthnum);
                    String month_name = month_date.format(cal.getTime());

                    city = employee.getLocation().getCity();
                    country = employee.getLocation().getCountry();
                    phone = employee.getPhone();
                    cell = employee.getCell();
                    email = employee.getEmail();

                    String latitude = employee.getLocation().getCoordinates().getLatitude();
                    String longitude = employee.getLocation().getCoordinates().getLongitude();

                    new DownloadImageFromInternet(photo_profile).execute(image_path);

                    employee_name.setText(first_name + " " + last_name);
                    employee_registered.setText("Member since: " + month_name + " " + datePart[0]);
                    employee_location.setText(city + ", " + country);
                    employee_phone.setText(phone + " / " + cell);
                    employee_email.setText(email);

                    SupportMapFragment mapFragment = (SupportMapFragment) getSupportFragmentManager().findFragmentById(R.id.map);

                    mapFragment.getMapAsync(new OnMapReadyCallback() {
                        @Override
                        public void onMapReady(@NonNull GoogleMap googleMap) {
                            map = googleMap;

                            LatLng location = new LatLng(Double.parseDouble(latitude), Double.parseDouble(longitude));
                            map.addMarker(new MarkerOptions().position(location).title("Employee Location"));
                            map.moveCamera(CameraUpdateFactory.newLatLng(location));
                        }
                    });
                    add_btn.setEnabled(true);
                }
            }

            @Override
            public void onFailure(Call<resModel> call, Throwable t) {
                Toast.makeText(EmployeeDetailActivity.this, t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });

        add_btn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                DBHelper dbHelper = new DBHelper(EmployeeDetailActivity.this);
                dbHelper.insertData(employeeID, first_name, last_name, city, country, phone, cell, email, image_path);
                Toast.makeText(EmployeeDetailActivity.this, "Employee has been added!", Toast.LENGTH_SHORT).show();
                finish();
            }
        });
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        finish();
    }

    private class DownloadImageFromInternet extends AsyncTask<String, Void, Bitmap> {
        ImageView imageView;

        public DownloadImageFromInternet(ImageView imageView) {
            this.imageView = imageView;
        }

        protected Bitmap doInBackground(String... urls) {
            String imageURL = urls[0];
            Bitmap bimage = null;
            try {
                InputStream in = new java.net.URL(imageURL).openStream();
                bimage = BitmapFactory.decodeStream(in);

            } catch (Exception e) {
                Log.e("Error Message", e.getMessage());
                e.printStackTrace();
            }
            return bimage;
        }

        protected void onPostExecute(Bitmap result) {
            imageView.setImageBitmap(result);
        }
    }
}